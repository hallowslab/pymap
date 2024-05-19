from django.http.response import HttpResponseRedirect
from django.urls import reverse


def staff_only(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        admin_login_url: str = reverse("admin:login")
        admin_logout_url: str = reverse("admin:logout")

        # Check if the request is to the admin page (but not login or logout) and if the user is not a staff member
        if (
            request.path.startswith(reverse("admin:index"))
            and request.path not in [admin_login_url, admin_logout_url]
            and not request.user.is_staff
        ):
            # Redirect non-staff users to the index page
            response = HttpResponseRedirect(reverse("migrator:index"))
            response.set_cookie(
                "privilege_warning", "true", max_age=10
            )  # Set a short-lived cookie
            return response

        # Proceed with the response if the user is staff or not accessing admin page
        response = get_response(request)
        return response

    return middleware
