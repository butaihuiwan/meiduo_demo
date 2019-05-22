from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer, BadData


# Create your models here.

class User(AbstractUser):

    mobile  = models.CharField(max_length=11, unique=True,verbose_name='手机号')

    email_active = models.BooleanField(default=False,verbose_name='邮箱是否激活')


    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

        # 在 str 魔法方法中, 返回用户名称

    def __str__(self):
        return self.username

    def generate_verify_email_url(self):
        """
        生成邮箱验证链接
        :param user: 当前登录用户
        :return: verify_url
        """
        # 调用 itsdangerous 中的类,生成对象
        # 有效期: 1天
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=60 * 60 * 24)
        # 拼接参数
        data = {'user_id': self.id, 'email': self.email}
        # 生成 token 值, 这个值是 bytes 类型, 所以解码为 str:
        token = serializer.dumps(data).decode()
        # 拼接 url
        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
        # 返回
        return verify_url

    @staticmethod
    def check_cerify_emile_token(token):
        """
           验证token并提取user
           :param token: 用户信息签名后的结果
           :return: user, None
           """
        # 调用 itsdangerous 类,生成对象
        # 邮件验证链接有效期：一天
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 60 * 60 * 24)

        try:
            # 解析传入的token值，获取数据data
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            # 如果有值，则获取
            user_id = data.get('user_id')
            email = data.get('email')

        # 获取到值之后，尝试从User表中获取对应的用户

        try:
            user = User.objects.get(id=user_id,email=email)
        except User.DoesNotExist:
            return None
        else:
            return user