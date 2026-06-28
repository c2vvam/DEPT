import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import QuerySet, Count
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Profile
from .models import Need, Group, GroupMember, ChatMessage, Notification
from aimatch.services.match_service import (
    submit_need,
    accept_group_choice,
    decline_group_choices,
    join_group_directly,
    leave_group,
    check_group_timers
)





@require_POST
def needs_create_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        data = json.loads(request.body)
        need_type: str = data.get("type", "")
        detail_text: str = data.get("detail_text", "")
        size_category: str = data.get("size_category", "")

        if not need_type or not detail_text or not size_category:
            return JsonResponse({"error": "필수 필드가 누락되었습니다."}, status=400)

        need = submit_need(
            user=request.user,
            need_type=need_type,
            detail_text=detail_text,
            size_category=size_category
        )
        return JsonResponse({
            "status": "accepted",
            "need_id": need.id,
            "message": "매칭 신청이 정상적으로 접수되었습니다."
        }, status=202)

    except json.JSONDecodeError:
        return JsonResponse({"error": "올바르지 않은 JSON 형식입니다."}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": e.message if hasattr(e, 'message') else str(e)}, status=400)


@require_GET
def needs_match_result_view(request: HttpRequest, need_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    need = get_object_or_404(Need, id=need_id)
    if need.user != request.user:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    response_data = {
        "need_id": need.id,
        "status": need.status,
    }

    if need.status == 'matched_waiting':
        recommended_groups_data = []
        for item in need.recommended_groups:
            try:
                g = Group.objects.get(id=item["group_id"])
                recommended_groups_data.append({
                    "group_id": g.id,
                    "title": g.title,
                    "tags": [t.strip() for t in g.tags.split(",") if t.strip()] if g.tags else [],
                    "current_members": g.members.count(),
                    "max_members": g.max_size,
                    "reasoning": item["reasoning"]
                })
            except Group.DoesNotExist:
                continue
        response_data["recommended_groups"] = recommended_groups_data

    return JsonResponse(response_data)


@require_POST
def needs_accept_group_view(request: HttpRequest, need_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    need = get_object_or_404(Need, id=need_id)
    if need.user != request.user:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    try:
        data = json.loads(request.body)
        group_id_val = data.get("group_id")
        if not group_id_val:
            return JsonResponse({"error": "그룹 ID가 필요합니다."}, status=400)

        group_id = int(group_id_val)

        recommended_ids = [item["group_id"] for item in need.recommended_groups]
        if group_id not in recommended_ids:
            return JsonResponse({"error": "추천된 그룹만 수락할 수 있습니다."}, status=400)

        accept_group_choice(need, group_id)
        return JsonResponse({"status": "success", "message": "그룹 참가가 완료되었습니다."})

    except json.JSONDecodeError:
        return JsonResponse({"error": "올바르지 않은 JSON 형식입니다."}, status=400)
    except ValidationError as e:
        return JsonResponse({"error": e.message if hasattr(e, 'message') else str(e)}, status=400)


@require_POST
def needs_decline_group_view(request: HttpRequest, need_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    need = get_object_or_404(Need, id=need_id)
    if need.user != request.user:
        return JsonResponse({"error": "권한이 없습니다."}, status=403)

    try:
        decline_group_choices(need)
        return JsonResponse({"status": "success", "message": "매칭 거절 후 신규 그룹이 생성되어 대기 상태로 전환되었습니다."})
    except ValidationError as e:
        return JsonResponse({"error": e.message if hasattr(e, 'message') else str(e)}, status=400)


@require_GET
def groups_list_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    check_group_timers()

    groups = Group.objects.filter(status__in=['forming', 'min_reached_grace']).annotate(
        member_count=Count('members')
    )

    valid_groups = []
    for g in groups:
        if g.member_count < g.max_size:
            valid_groups.append(g)

    now = timezone.now()

    def get_sort_key(g: Group) -> tuple:
        remaining_spots = g.max_size - g.member_count
        is_one_spot_left = 0 if remaining_spots == 1 else 1

        time_remaining = 999999999.0
        if g.status == 'min_reached_grace' and g.min_reached_at:
            elapsed = (now - g.min_reached_at).total_seconds()
            time_remaining = max(0.0, 1800.0 - elapsed)
        elif g.status == 'forming' and g.member_count >= 2:
            elapsed = (now - g.last_member_change_at).total_seconds()
            time_remaining = max(0.0, 43200.0 - elapsed)

        return (is_one_spot_left, time_remaining, -g.created_at.timestamp())

    valid_groups.sort(key=get_sort_key)

    data = []
    for g in valid_groups[:50]:
        data.append({
            "id": g.id,
            "type": g.type,
            "type_display": g.get_type_display(),
            "size_category": g.size_category,
            "title": g.title,
            "tags": [t.strip() for t in g.tags.split(",") if t.strip()] if g.tags else [],
            "current_members": g.member_count,
            "max_members": g.max_size,
            "status": g.status,
            "created_at": g.created_at.isoformat()
        })

    return JsonResponse({"groups": data})


@require_GET
def groups_detail_view(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    group = get_object_or_404(Group, id=group_id)

    # Check if the user is a member of the group
    is_member = group.members.filter(user=request.user).exists()
    if not is_member:
        return JsonResponse({"error": "접근 권한이 없습니다."}, status=403)

    members_data = []
    for m in group.members.all():
        profile = m.user.profile
        is_self = (m.user == request.user)

        real_nickname = profile.nickname if profile.nickname else m.user.username
        name = m.user.first_name if m.user.first_name else real_nickname
        real_img = profile.profile_image_url if profile.profile_image_url else ""

        members_data.append({
            "user_id": m.user.id,
            "name": name,
            "department": profile.department,
            "admission_year": profile.admission_year,
            "profile_image_url": real_img,
            "is_blurred": False,
            "is_self": is_self,
            "joined_at": m.joined_at.isoformat()
        })

    return JsonResponse({
        "id": group.id,
        "type": group.type,
        "type_display": group.get_type_display(),
        "size_category": group.size_category,
        "title": group.title,
        "tags": [t.strip() for t in group.tags.split(",") if t.strip()] if group.tags else [],
        "status": group.status,
        "current_members": len(members_data),
        "max_members": group.max_size,
        "created_at": group.created_at.isoformat(),
        "members": members_data
    })


@require_POST
def groups_join_view(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        join_group_directly(request.user, group_id)
        return JsonResponse({"status": "success", "message": "그룹에 직접 참여하였습니다."})
    except ValidationError as e:
        return JsonResponse({"error": e.message if hasattr(e, 'message') else str(e)}, status=400)


@require_POST
def groups_leave_view(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        leave_group(request.user, group_id)
        return JsonResponse({"status": "success", "message": "그룹 대기방을 나갔습니다."})
    except ValidationError as e:
        return JsonResponse({"error": e.message if hasattr(e, 'message') else str(e)}, status=400)


def matching_board_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('accounts:login')
    return render(request, 'aimatch/matching.html')


@require_GET
def user_status_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    active_need = Need.objects.filter(
        user=request.user,
        status__in=['pending_matching', 'matched_waiting', 'registered']
    ).first()

    active_member = GroupMember.objects.filter(
        user=request.user,
        group__status__in=['forming', 'min_reached_grace', 'confirmed', 'closed_timeout']
    ).first()

    response_data = {
        "need": None,
        "group": None,
    }

    if active_need:
        recommended_groups_data = []
        if active_need.status == 'matched_waiting':
            for item in active_need.recommended_groups:
                try:
                    g = Group.objects.get(id=item["group_id"])
                    recommended_groups_data.append({
                        "group_id": g.id,
                        "title": g.title,
                        "tags": [t.strip() for t in g.tags.split(",") if t.strip()] if g.tags else [],
                        "current_members": g.members.count(),
                        "max_members": g.max_size,
                        "reasoning": item["reasoning"]
                    })
                except Group.DoesNotExist:
                    continue
        else:
            recommended_groups_data = active_need.recommended_groups

        response_data["need"] = {
            "id": active_need.id,
            "type": active_need.type,
            "type_display": active_need.get_type_display(),
            "detail_text": active_need.detail_text,
            "size_category": active_need.size_category,
            "status": active_need.status,
            "recommended_groups": recommended_groups_data
        }

    if active_member:
        g = active_member.group
        check_group_timers()
        g.refresh_from_db()
        response_data["group"] = {
            "id": g.id,
            "title": g.title,
            "type": g.type,
            "type_display": g.get_type_display(),
            "size_category": g.size_category,
            "tags": [t.strip() for t in g.tags.split(",") if t.strip()] if g.tags else [],
            "status": g.status,
            "current_members": g.members.count(),
            "max_members": g.max_size
        }

    return JsonResponse(response_data)


@require_GET
def chat_history_view(request: HttpRequest, group_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    member = GroupMember.objects.filter(group_id=group_id, user=request.user).first()
    if not member:
        return JsonResponse({"error": "접근 권한이 없습니다."}, status=403)

    messages = ChatMessage.objects.filter(
        group_id=group_id,
        created_at__gte=member.joined_at
    ).select_related('sender__profile').order_by('created_at')

    data = []
    for msg in messages:
        sender = msg.sender
        profile = sender.profile
        real_nickname = profile.nickname if profile.nickname else sender.username
        name = sender.first_name if sender.first_name else real_nickname
        admission_year_text = f"{str(profile.admission_year)[2:]}학번" if profile.admission_year else ""

        data.append({
            "id": msg.id,
            "sender_id": sender.id,
            "sender_name": name,
            "sender_dept": profile.department,
            "sender_year": admission_year_text,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        })

    return JsonResponse({"messages": data})


@ensure_csrf_cookie
@require_GET
def notifications_list_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:30]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    data = []
    for n in notifications:
        data.append({
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        })

    return JsonResponse({
        "notifications": data,
        "unread_count": unread_count
    })


@require_POST
def notifications_mark_read_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return JsonResponse({"error": "로그인이 필요합니다."}, status=401)

    try:
        body = json.loads(request.body)
        notification_id = body.get('notification_id')
    except (json.JSONDecodeError, TypeError):
        notification_id = request.POST.get('notification_id')

    if notification_id:
        Notification.objects.filter(user=request.user, id=notification_id).delete()
    else:
        Notification.objects.filter(user=request.user, is_read=False).delete()

    return JsonResponse({"status": "success"})


