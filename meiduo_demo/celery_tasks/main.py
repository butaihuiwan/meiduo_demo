from celery import Celery
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_demo.settings.dev'

# 用celery创建对象：

celery_app = Celery('meiduo')
celery_app.config_from_object('celery_tasks.config')


celery_app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])