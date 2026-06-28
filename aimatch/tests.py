import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from aimatch.models import Need, Group, GroupMember, Notification, ChatMessage
from aimatch.services.match_service import (
    submit_need,
    accept_group_choice,
    decline_group_choices,
    join_group_directly,
    leave_group,
    check_group_timers
)


class MatchServiceTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        self.user1: User = User.objects.create_user(
            username='user1@pusan.ac.kr',
            email='user1@pusan.ac.kr',
            password='Password123',
            first_name='김철수'
        )
        from accounts.models import Profile
        Profile.objects.create(
            user=self.user1,
            nickname="김철수",
            department="자유전공학부",
            admission_year=2021
        )

        self.user2: User = User.objects.create_user(
            username='user2@pusan.ac.kr',
            email='user2@pusan.ac.kr',
            password='Password123',
            first_name='이영희'
        )
        Profile.objects.create(
            user=self.user2,
            nickname="이영희",
            department="자유전공학부",
            admission_year=2022
        )

        self.user3: User = User.objects.create_user(
            username='user3@pusan.ac.kr',
            email='user3@pusan.ac.kr',
            password='Password123',
            first_name='박민수'
        )
        Profile.objects.create(
            user=self.user3,
            nickname="박민수",
            department="자유전공학부",
            admission_year=2023
        )

    def test_submit_need_and_restrictions(self) -> None:
        need = submit_need(
            user=self.user1,
            need_type='study',
            detail_text='파이썬 Django 기초 스터디원 구해요.',
            size_category='small'
        )
        self.assertEqual(need.status, 'pending_matching')

        with self.assertRaises(ValidationError):
            submit_need(
                user=self.user1,
                need_type='study',
                detail_text='파이썬 Django 기초 스터디원 구해요. 중복가입 불가능 테스트.',
                size_category='small'
            )

    def test_need_text_length_validation(self) -> None:
        with self.assertRaises(ValidationError):
            submit_need(self.user1, 'study', '짧음', 'small')

        with self.assertRaises(ValidationError):
            submit_need(self.user1, 'study', 'a' * 501, 'small')

    def test_matching_logic_no_candidates(self) -> None:
        need = submit_need(
            user=self.user1,
            need_type='study',
            detail_text='파이썬 Django 기초 스터디원 구해요.',
            size_category='small'
        )
        from aimatch.services.match_service import run_matching_pipeline
        run_matching_pipeline(need.id)

        need.refresh_from_db()
        self.assertEqual(need.status, 'registered')

        group = Group.objects.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.type, 'study')
        self.assertEqual(group.status, 'forming')
        self.assertEqual(group.members.count(), 1)
        self.assertTrue(GroupMember.objects.filter(group=group, user=self.user1).exists())

    def test_matching_logic_with_candidates(self) -> None:
        candidate_group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )
        GroupMember.objects.create(group=candidate_group, user=self.user2)

        need = submit_need(
            user=self.user1,
            need_type='study',
            detail_text='Django Python 기초 스터디 구하고 있습니다.',
            size_category='small'
        )
        from aimatch.services.match_service import run_matching_pipeline
        run_matching_pipeline(need.id)

        need.refresh_from_db()
        self.assertEqual(need.status, 'matched_waiting')
        self.assertEqual(len(need.recommended_groups), 1)
        self.assertEqual(need.recommended_groups[0]["group_id"], candidate_group.id)

    def test_accept_group_choice(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )
        GroupMember.objects.create(group=group, user=self.user2)

        need = submit_need(
            user=self.user1,
            need_type='study',
            detail_text='Django Python 기초 스터디 구하고 있습니다.',
            size_category='small'
        )
        need.status = 'matched_waiting'
        need.recommended_groups = [{"group_id": group.id, "rank": 1, "reasoning": "좋은 그룹"}]
        need.save()

        accept_group_choice(need, group.id)

        need.refresh_from_db()
        group.refresh_from_db()

        self.assertEqual(need.status, 'matched')
        self.assertEqual(group.members.count(), 2)
        self.assertEqual(group.status, 'min_reached_grace')
        self.assertIsNotNone(group.min_reached_at)

        from accounts.models import Profile
        user4 = User.objects.create_user(username='user4@pusan.ac.kr', password='Password123')
        Profile.objects.create(user=user4, nickname="정지우")

        join_group_directly(self.user3, group.id)
        group.refresh_from_db()
        self.assertEqual(group.status, 'min_reached_grace')

        join_group_directly(user4, group.id)
        group.refresh_from_db()
        self.assertEqual(group.status, 'confirmed')

        notifications = Notification.objects.filter(user=self.user1)
        self.assertTrue(notifications.exists())

    def test_decline_group_choices(self) -> None:
        need = submit_need(
            user=self.user1,
            need_type='study',
            detail_text='Django Python 기초 스터디 구하고 있습니다.',
            size_category='small'
        )
        decline_group_choices(need)
        need.refresh_from_db()
        self.assertEqual(need.status, 'registered')
        self.assertEqual(Group.objects.count(), 1)

    def test_leave_group_and_re_matching(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )
        GroupMember.objects.create(group=group, user=self.user1)
        GroupMember.objects.create(group=group, user=self.user2)

        need = Need.objects.create(
            user=self.user1,
            type='study',
            detail_text='Django Python 기초 스터디 구하고 있습니다.',
            size_category='small',
            status='matched'
        )

        leave_group(self.user1, group.id)

        group.refresh_from_db()
        need.refresh_from_db()

        self.assertEqual(group.members.count(), 1)
        self.assertEqual(group.status, 'forming')
        self.assertIsNone(group.min_reached_at)
        self.assertEqual(need.status, 'expired')

    def test_leave_group_and_delete_empty_group(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )
        GroupMember.objects.create(group=group, user=self.user1)

        leave_group(self.user1, group.id)

        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(id=group.id)

    def test_check_group_timers_grace_timeout(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='min_reached_grace',
            min_reached_at=timezone.now() - timedelta(minutes=31)
        )
        GroupMember.objects.create(group=group, user=self.user1)
        GroupMember.objects.create(group=group, user=self.user2)

        need1 = Need.objects.create(user=self.user1, type='study', size_category='small', status='matched')
        need2 = Need.objects.create(user=self.user2, type='study', size_category='small', status='registered')

        check_group_timers()

        group.refresh_from_db()
        self.assertEqual(group.status, 'closed_timeout')

        need1.refresh_from_db()
        need2.refresh_from_db()
        self.assertEqual(need1.status, 'matched')
        self.assertEqual(need2.status, 'registered')

        leave_group(self.user1, group.id)
        need1.refresh_from_db()
        self.assertEqual(need1.status, 'pending_matching')
        self.assertEqual(group.members.count(), 1)

        leave_group(self.user2, group.id)
        need2.refresh_from_db()
        self.assertEqual(need2.status, 'pending_matching')
        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(id=group.id)

    def test_check_group_timers_forming_timeout(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='medium',
            title='Django 중급 스터디',
            tags='Django,Python',
            status='forming',
            last_member_change_at=timezone.now() - timedelta(hours=13)
        )
        GroupMember.objects.create(group=group, user=self.user1)
        GroupMember.objects.create(group=group, user=self.user2)

        need1 = Need.objects.create(user=self.user1, type='study', size_category='medium', status='matched')
        need2 = Need.objects.create(user=self.user2, type='study', size_category='medium', status='registered')

        check_group_timers()

        group.refresh_from_db()
        self.assertEqual(group.status, 'closed_timeout')

        need1.refresh_from_db()
        need2.refresh_from_db()
        self.assertEqual(need1.status, 'matched')
        self.assertEqual(need2.status, 'registered')

        leave_group(self.user1, group.id)
        need1.refresh_from_db()
        self.assertEqual(need1.status, 'pending_matching')
        self.assertEqual(group.members.count(), 1)

        leave_group(self.user2, group.id)
        need2.refresh_from_db()
        self.assertEqual(need2.status, 'pending_matching')
        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(id=group.id)


class MatchAPIViewsTests(TestCase):
    def setUp(self) -> None:
        self.client: Client = Client()
        self.user1: User = User.objects.create_user(
            username='user1@pusan.ac.kr',
            email='user1@pusan.ac.kr',
            password='Password123',
            first_name='김철수'
        )
        from accounts.models import Profile
        Profile.objects.create(
            user=self.user1,
            nickname="김철수",
            department="자유전공학부",
            admission_year=2021
        )

        self.user2: User = User.objects.create_user(
            username='user2@pusan.ac.kr',
            email='user2@pusan.ac.kr',
            password='Password123',
            first_name='이영희'
        )
        Profile.objects.create(
            user=self.user2,
            nickname="이영희",
            department="자유전공학부",
            admission_year=2022
        )

    def test_api_needs_create(self) -> None:
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('aimatch:needs_create'),
            data=json.dumps({
                "type": "study",
                "detail_text": "자유전공학부 파이썬 Django 입문 스터디원을 모집합니다.",
                "size_category": "small"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 202)
        res_data = response.json()
        self.assertEqual(res_data["status"], "accepted")
        self.assertIn("need_id", res_data)

    def test_api_needs_create_anonymous_denied(self) -> None:
        response = self.client.post(
            reverse('aimatch:needs_create'),
            data=json.dumps({
                "type": "study",
                "detail_text": "자유전공학부 파이썬 Django 입문 스터디원을 모집합니다.",
                "size_category": "small"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_api_needs_match_result_and_idor_protection(self) -> None:
        self.client.force_login(self.user1)
        need = submit_need(self.user1, 'study', '파이썬 Django 기초 스터디원 구해요.', 'small')

        response = self.client.get(reverse('aimatch:needs_match_result', args=[need.id]))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user2)
        response = self.client.get(reverse('aimatch:needs_match_result', args=[need.id]))
        self.assertEqual(response.status_code, 403)

    def test_api_groups_list_and_detail(self) -> None:
        self.client.force_login(self.user1)

        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )
        GroupMember.objects.create(group=group, user=self.user2)

        response = self.client.get(reverse('aimatch:groups_list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["groups"]), 1)
        self.assertEqual(data["groups"][0]["title"], 'Django 기초 스터디')

        # Since user1 is not a member, groups_detail should return 403 Forbidden.
        response = self.client.get(reverse('aimatch:groups_detail', args=[group.id]))
        self.assertEqual(response.status_code, 403)

        # After user1 joins, groups_detail should return 200 and show details.
        GroupMember.objects.create(group=group, user=self.user1)
        response = self.client.get(reverse('aimatch:groups_detail', args=[group.id]))
        self.assertEqual(response.status_code, 200)
        detail = response.json()
        self.assertEqual(len(detail["members"]), 2)
        self.assertEqual(detail["members"][0]["name"], "이영희")
        self.assertEqual(detail["members"][0]["department"], "자유전공학부")
        self.assertEqual(detail["members"][0]["admission_year"], 2022)
        self.assertFalse(detail["members"][0]["is_blurred"])

    def test_api_groups_join_and_leave(self) -> None:
        self.client.force_login(self.user1)
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )

        response = self.client.post(reverse('aimatch:groups_join', args=[group.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupMember.objects.filter(group=group, user=self.user1).exists())

        response = self.client.post(reverse('aimatch:groups_leave', args=[group.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMember.objects.filter(group=group, user=self.user1).exists())

    def test_api_chat_history(self) -> None:
        group = Group.objects.create(
            type='study',
            size_category='small',
            title='Django 기초 스터디',
            tags='Django,Python',
            status='forming'
        )

        member1 = GroupMember.objects.create(group=group, user=self.user1)
        member1.joined_at = timezone.now() - timedelta(minutes=10)
        member1.save()

        msg1 = ChatMessage.objects.create(
            group=group,
            sender=self.user1,
            content="안녕하세요! user1입니다.",
        )
        msg1.created_at = timezone.now() - timedelta(minutes=5)
        msg1.save()

        member2 = GroupMember.objects.create(group=group, user=self.user2)
        member2.joined_at = timezone.now() - timedelta(minutes=2)
        member2.save()

        msg2 = ChatMessage.objects.create(
            group=group,
            sender=self.user2,
            content="반갑습니다! user2입니다."
        )

        # user1 fetches history (should see both messages)
        self.client.force_login(self.user1)
        response = self.client.get(reverse('aimatch:chat_history', args=[group.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 2)
        self.assertEqual(data["messages"][0]["content"], "안녕하세요! user1입니다.")
        self.assertEqual(data["messages"][1]["content"], "반갑습니다! user2입니다.")

        # user2 fetches history (should see only msg2)
        self.client.force_login(self.user2)
        response = self.client.get(reverse('aimatch:chat_history', args=[group.id]))
        self.assertEqual(response.status_code, 200)
        data2 = response.json()
        self.assertEqual(len(data2["messages"]), 1)
        self.assertEqual(data2["messages"][0]["content"], "반갑습니다! user2입니다.")

        # user3 is not a member (should get 403 forbidden)
        user3 = User.objects.create_user(
            username='user3@pusan.ac.kr',
            email='user3@pusan.ac.kr',
            password='Password123',
            first_name='박민수'
        )
        from accounts.models import Profile
        Profile.objects.create(
            user=user3,
            nickname="박민수",
            department="자유전공학부",
            admission_year=2023
        )
        self.client.force_login(user3)
        response = self.client.get(reverse('aimatch:chat_history', args=[group.id]))
        self.assertEqual(response.status_code, 403)

