from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
# from core.models import TblSchoolid

# Create your models here.
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user_object(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        return user

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        user = self._create_user_object(username, email, password, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    # TblUser のカラムを追加
    user_simei = models.CharField(max_length=100, default='未設定')
    # s = models.ForeignKey('TblSchoolid', on_delete=models.CASCADE)
    u_auth = models.SmallIntegerField(
        choices=[
            (-1, '保護者'),
            (0, '生徒'),
            (1, '講師'),
            (2, '教室'),
        ],
        default=0
    )
    l_login_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    update_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    reg_date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    objects = CustomUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username


