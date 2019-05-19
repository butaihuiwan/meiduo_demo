from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):

    mobile  = models.CharField(max_length=11, unique=True,verbose_name='手机号')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

        # 在 str 魔法方法中, 返回用户名称

    def __str__(self):
        return self.username