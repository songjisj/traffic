# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin sqlcustom [app_label]'
# into your database.


from django.db import models


class Controller(models.Model):
    cid = models.AutoField(primary_key=True)
    cname = models.CharField(unique=True, max_length=32)
    lastupdate = models.DateTimeField(db_column='lastUpdate')  # Field name made lowercase.
    opstate = models.SmallIntegerField()
    opstatetime = models.DateTimeField(db_column='opstateTime')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'controller' 


class ControllerConfig(models.Model):
    fk_cid = models.ForeignKey(Controller, db_column='fk_cid', primary_key=True)
    cfghash = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'controller_config'


class ControllerConfigDet(models.Model):
    fk_cid = models.ForeignKey(Controller, db_column='fk_cid')
    idx = models.IntegerField()
    sgidx = models.IntegerField()
    name = models.CharField(max_length=18)

    class Meta:
        managed = False
        db_table = 'controller_config_det'
        unique_together = (('fk_cid', 'idx'),)


class ControllerConfigSg(models.Model):
    fk_cid = models.ForeignKey(Controller, db_column='fk_cid')
    idx = models.IntegerField()
    name = models.CharField(max_length=12)

    class Meta:
        managed = False
        db_table = 'controller_config_sg'
        unique_together = (('fk_cid', 'idx'),)


class TfRaw(models.Model):
    fk_cid = models.IntegerField(blank=True, null=True)
    tt = models.DateTimeField(blank=True, null=True)
    seq = models.IntegerField(blank=True, null=True)
    grint = models.CharField(max_length=64, blank=True, null=True)
    dint = models.CharField(max_length=128, blank=True, null=True)
    row_id = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'tf_raw'


class TfRawOriginal(models.Model):
    fk_cid = models.ForeignKey(Controller, db_column='fk_cid')
    tt = models.DateTimeField()
    seq = models.IntegerField()
    grint = models.CharField(max_length=64)
    dint = models.CharField(max_length=128)

    class Meta:
        managed = False
        db_table = 'tf_raw_original'
        unique_together = (('fk_cid', 'tt'),)
