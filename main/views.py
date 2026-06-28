from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from accounts.models import Profile

def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        # Get authenticated user profile
        profile: Profile = request.user.profile
        school: str = "부산대학교"
        department: str = profile.department if profile.department else "자유전공학부"

        from aimatch.models import GroupMember
        active_membership = GroupMember.objects.filter(
            user=request.user,
            group__status__in=['forming', 'min_reached_grace', 'confirmed']
        ).select_related('group').first()

        my_group = active_membership.group if active_membership else None
        my_group_pct = 0
        my_group_tags = []

        if my_group:
            current_mem = my_group.members.count()
            max_mem = my_group.max_size
            my_group_pct = int((current_mem / max_mem) * 100) if max_mem > 0 else 0
            if my_group.tags:
                my_group_tags = [t.strip() for t in my_group.tags.split(",") if t.strip()]

        context = {
            'school': school,
            'department': department,
            'profile': profile,
            'my_group': my_group,
            'my_group_pct': my_group_pct,
            'my_group_tags': my_group_tags
        }
        return render(request, 'main/dashboard.html', context)
    else:
        # Render public landing page for guest users
        return render(request, 'main/index.html')



