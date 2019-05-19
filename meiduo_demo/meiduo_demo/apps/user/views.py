import re

from django import http
from django.contrib.auth import login
from django.db import DatabaseError
from django.urls import reverse
from django_redis import  get_redis_connection


from meiduo_demo.utils.response_code import RETCODE
from . models import User
from django.shortcuts import render, redirect

# Create your views here.
from django.views import View


class Register(View):

    def get(self,request):
        pass

        return render(request, 'register.html')


    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        if not all([username, password, password2, mobile, allow,sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 对短信验证码进行校验
        redis_conn = get_redis_connection('verify_code')
        redis_conn_server = redis_conn.get('sms_%s' % mobile)
        if redis_conn_server is None:
            return render(request,'register.html',{'content':'输入验证码失效'})
        if sms_code_client != redis_conn_server.decode():
            return http.HttpResponseForbidden('输入短信验证码错误')

        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})


        login(request,user)
        # 响应注册结果
        # return http.HttpResponse('注册成功，重定向到首页')

        return redirect(reverse('contents:index'))


class UsernameCountView(View):

    def get(self,request, username):
         count =    User.objects.filter(username= username).count()
         return http.JsonResponse({'code': RETCODE.OK,
                                   'errmsg': 'ok',
                                   'count':'count'})



class MobileCountView(View):
    """
    判断手机号是否重复注册
    """
    def get(self,request,mobile):
        """

        :param request: 请求对象
        : param mobile: 手机号
        :return: JSON
        """

        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code':RETCODE.OK,
                                  'errmsg':'ok',
                                  'count':'count'})


