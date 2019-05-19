# Create your views here.
import random

from  django import http
from django.views import View


from meiduo_demo.apps.verifications import constants
from meiduo_demo.libs.captcha.captcha import captcha
from django_redis import  get_redis_connection

from meiduo_demo.libs.yuntongxun.ccp_sms import CCP
from meiduo_demo.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class ImageCodeView(View):
    """
    图形验证码
    """
    def get(self,request,uuid):
        """

        :param request:
        :param uuid:
        :return: image/jpg
        """
        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('verify_code')

        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXOIRES,text)

        return http.HttpResponse(image,content_type='image/jpg')




#  短信验证码
class SMSCodeView(View):
    """短信验证码"""
    def get(self,request,mobile):
        # 3.创建连接redis的对象
        # 判断是否在60秒处第二次发送短信
        redis_conn = get_redis_connection('verify_code')
        sms_flag_get = redis_conn.get('send_flag_%s' % mobile)
        # if sms_flag_get:
        #     return http.JsonResponse({'code':RETCODE.THROTTLINGERR,
        #                               'errmsg':'发送短信过于频繁'})
        """

        :param request:  请求对象
        :param mobile: 手机号
        :return: JSON
        """
    # 1.接受参数: 图形验证码， 唯一编号
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

    # 参数校验
        if not all([image_code_client,uuid]):
            return http.JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'缺少必要参数'})



    # 4.提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)

        # 判断图形验证码是否过期或不存在
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg':'图形验证码失效'})

    # 5.删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('image_%s' % uuid)

        except Exception as e:

            logger.error(e)

    # 6.对比图形验证码
        image_code_server = image_code_server.decode() # bytes 转字符串

        if image_code_client.lower() != image_code_server.lower(): # 转小写后比较
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg'
                                      :'输入的图形验证码错误'})

    # 7. 生成短信验证码：生成6位数验证码
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code)

        # 性能优化，创建管道
        pl = redis_conn.pipeline()

        """
        8.保存短信验证码
        短信验证码有效期 单位： 秒
        IMAGE_CODE_REDIS_EXOIRES = 300
        """
        pl.setex('sms_%s' % mobile, constants.IMAGE_CODE_REDIS_EXOIRES,sms_code)

        # redis 中增加一个键值, 防止频繁发送信息
        pl.setex('send_flag_%s'% mobile , constants.IMAGE_CODE_REDIS_EXOIRES,1)

        # 执行管道
        pl.execute()


    # 9.发送短信验证码
        # 短信模板

        # CCP().send_template_sms(mobile,[sms_code, constants.SMS_CODE_REDIS_EXPIRES],1)
        # from celery_tasks.sms.tasks import send_sms_code
        # send_sms_code.delay(mobile, sms_code)
    # 10 响应结果

        return http.JsonResponse({'code':RETCODE.OK,'errmsg':'发送短信成功'})
