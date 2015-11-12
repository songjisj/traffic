# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Controller',
            fields=[
                ('cid', models.AutoField(primary_key=True, serialize=False)),
                ('cname', models.CharField(unique=True, max_length=32)),
                ('lastupdate', models.DateTimeField(db_column='lastUpdate')),
                ('opstate', models.SmallIntegerField()),
                ('opstatetime', models.DateTimeField(db_column='opstateTime')),
            ],
            options={
                'managed': False,
                'db_table': 'controller',
            },
        ),
        migrations.CreateModel(
            name='ControllerConfigDet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('idx', models.IntegerField()),
                ('sgidx', models.IntegerField()),
                ('name', models.CharField(max_length=18)),
            ],
            options={
                'managed': False,
                'db_table': 'controller_config_det',
            },
        ),
        migrations.CreateModel(
            name='ControllerConfigSg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('idx', models.IntegerField()),
                ('name', models.CharField(max_length=12)),
            ],
            options={
                'managed': False,
                'db_table': 'controller_config_sg',
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'managed': False,
                'db_table': 'django_migrations',
            },
        ),
        migrations.CreateModel(
            name='TfRaw',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('tt', models.DateTimeField()),
                ('seq', models.IntegerField()),
                ('grint', models.CharField(max_length=64)),
                ('dint', models.CharField(max_length=128)),
            ],
            options={
                'managed': False,
                'db_table': 'tf_raw',
            },
        ),
        migrations.CreateModel(
            name='ControllerConfig',
            fields=[
                ('fk_cid', models.ForeignKey(serialize=False, db_column='fk_cid', to='traffic.Controller', primary_key=True)),
                ('cfghash', models.CharField(null=True, blank=True, max_length=32)),
            ],
            options={
                'managed': False,
                'db_table': 'controller_config',
            },
        ),
    ]
