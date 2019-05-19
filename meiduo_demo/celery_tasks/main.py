from celery import Celery

# 用celery创建对象：

celery_app = Celery('meiduo')
celery_app.config_from_object('celery_tasks.config')


celery_app.autodiscover_tasks(['celery_tasks.sms'])