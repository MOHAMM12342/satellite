from django.db import models

class SchemaMigrations(models.Model):
    version = models.BigIntegerField(primary_key=True)
    dirty = models.BooleanField()

    class Meta:
        app_label='myapi'
        db_table = 'schema_migrations'
        verbose_name_plural = 'schema migrations'

class SatFiles(models.Model):
    id = models.IntegerField(primary_key=True)
    subsystem_id = models.SmallIntegerField()
    id_in_subsystem = models.IntegerField()
    cur_file_ver = models.IntegerField()
    last_down_seq_nr = models.BigIntegerField()
    last_up_seq_nr = models.BigIntegerField()
    updated_ts = models.DateTimeField()
    first_down_seq_nr = models.BigIntegerField(default=1)

    class Meta:
        app_label='myapi'
        db_table = 'sat_files'
        verbose_name_plural = 'sat files'

class DownloadEntriesArchive(models.Model):
    sat_file = models.ForeignKey(
        SatFiles,
        on_delete=models.RESTRICT,
        db_column='sat_file_id'
    )
    seq_nr = models.BigIntegerField()
    file_ver = models.IntegerField()
    received_ts = models.DateTimeField()
    archived_ts = models.DateTimeField()
    entry_nr = models.BigIntegerField()
    entry_data = models.BinaryField()

    class Meta:
        app_label='myapi'
        db_table = 'download_entries_archive'
        verbose_name_plural = 'download entries archive'
        constraints = [
            models.UniqueConstraint(
                fields=['sat_file', 'seq_nr'],
                name='download_entries_archive_pk'
            )
        ]

class UploadEntriesArchive(models.Model):
    sat_file = models.ForeignKey(
        SatFiles,
        on_delete=models.RESTRICT,
        db_column='sat_file_id'
    )
    seq_nr = models.BigIntegerField()
    file_ver = models.IntegerField()
    received_ts = models.DateTimeField()
    archived_ts = models.DateTimeField()
    entry_nr = models.BigIntegerField()
    entry_data = models.BinaryField()

    class Meta:
        app_label='myapi'
        db_table = 'upload_entries_archive'
        verbose_name_plural = 'upload entries archive'
        constraints = [
            models.UniqueConstraint(
                fields=['sat_file', 'seq_nr'],
                name='upload_entries_archive_pk'
            )
        ]

class DbFiles(models.Model):
    file_ver = models.IntegerField()
    sat_file = models.ForeignKey(
        SatFiles,
        on_delete=models.RESTRICT,
        db_column='sat_file_id'
    )
    init_ts = models.DateTimeField()
    update_ts = models.DateTimeField()
    type_id = models.SmallIntegerField()
    capacity = models.BigIntegerField()
    last_entry = models.BigIntegerField()
    sig = models.BigIntegerField()
    upload_hash = models.BinaryField()
    removed = models.BooleanField(default=False)

    class Meta:
        app_label='myapi'
        db_table = 'db_files'
        verbose_name_plural = 'db files'
        constraints = [
            models.UniqueConstraint(
                fields=['file_ver', 'sat_file'],
                name='db_files_pk'
            )
        ]

class DownloadGaps(models.Model):
    sat_file = models.ForeignKey(
        SatFiles,
        on_delete=models.RESTRICT,
        db_column='sat_file_id'
    )
    file_ver = models.IntegerField()
    start_entry = models.BigIntegerField()
    end_entry = models.BigIntegerField()
    gaps_ver = models.BigIntegerField()
    gaps_count = models.IntegerField()
    gaps_data = models.BinaryField()

    class Meta:
        app_label='myapi'
        db_table = 'download_gaps'
        verbose_name_plural = 'download gaps'
        constraints = [
            models.UniqueConstraint(
                fields=['sat_file', 'file_ver'],
                name='download_gaps_pk'
            )
        ]

class UploadGaps(models.Model):
    sat_file = models.ForeignKey(
        SatFiles,
        on_delete=models.RESTRICT,
        db_column='sat_file_id'
    )
    file_ver = models.IntegerField()
    start_entry = models.BigIntegerField()
    end_entry = models.BigIntegerField()
    gaps_ver = models.BigIntegerField()
    gaps_count = models.IntegerField()
    gaps_data = models.BinaryField()

    class Meta:
        app_label='myapi'
        db_table = 'upload_gaps'
        verbose_name_plural = 'upload gaps'
        constraints = [
            models.UniqueConstraint(
                fields=['sat_file', 'file_ver'],
                name='upload_gaps_pk'
            )
        ]



class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    is_staff = models.BooleanField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    date_joined = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class AuthtokenToken(models.Model):
    key = models.CharField(primary_key=True, max_length=40)
    created = models.DateTimeField()
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'authtoken_token'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'django_session'


class IprestrictIpgroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'iprestrict_ipgroup'


class IprestrictIplocation(models.Model):
    country_codes = models.CharField(max_length=2000)
    ip_group = models.ForeignKey(IprestrictIpgroup, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'iprestrict_iplocation'


class IprestrictIprange(models.Model):
    first_ip = models.GenericIPAddressField()
    cidr_prefix_length = models.SmallIntegerField(blank=True, null=True)
    last_ip = models.GenericIPAddressField(blank=True, null=True)
    ip_group = models.ForeignKey(IprestrictIpgroup, models.DO_NOTHING)
    description = models.CharField(max_length=500)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'iprestrict_iprange'


class IprestrictReloadrulesrequest(models.Model):
    at = models.DateTimeField()

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'iprestrict_reloadrulesrequest'


class IprestrictRule(models.Model):
    url_pattern = models.CharField(max_length=500)
    action = models.CharField(max_length=1)
    rank = models.IntegerField()
    ip_group = models.ForeignKey(IprestrictIpgroup, models.DO_NOTHING)
    reverse_ip_group = models.BooleanField()

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'iprestrict_rule'


class OtpStaticStaticdevice(models.Model):
    name = models.CharField(max_length=64)
    confirmed = models.BooleanField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    throttling_failure_count = models.IntegerField()
    throttling_failure_timestamp = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    last_used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'otp_static_staticdevice'


class OtpStaticStatictoken(models.Model):
    token = models.CharField(max_length=16)
    device = models.ForeignKey(OtpStaticStaticdevice, models.DO_NOTHING)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'otp_static_statictoken'


class OtpTotpTotpdevice(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    name = models.CharField(max_length=64)
    confirmed = models.BooleanField()
    key = models.CharField(max_length=80)
    step = models.IntegerField()
    t0 = models.BigIntegerField()
    digits = models.IntegerField()
    tolerance = models.IntegerField()
    drift = models.IntegerField()
    last_t = models.BigIntegerField()
    throttling_failure_timestamp = models.DateTimeField(blank=True, null=True)
    throttling_failure_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    last_used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label='authentification'
        managed = False
        db_table = 'otp_totp_totpdevice'
        unique_together = (('user', 'name'),)

