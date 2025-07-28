from django.db import models

class SchemaMigrations(models.Model):
    version = models.BigIntegerField(primary_key=True)
    dirty = models.BooleanField()

    class Meta:
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
        db_table = 'upload_gaps'
        verbose_name_plural = 'upload gaps'
        constraints = [
            models.UniqueConstraint(
                fields=['sat_file', 'file_ver'],
                name='upload_gaps_pk'
            )
        ]