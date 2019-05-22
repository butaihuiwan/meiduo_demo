from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^register/$', views.Register.as_view(),name='register'),
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^info/$', views.UserCenterInfoView.as_view(), name='info'),
    url(r'^emails/$', views.EmailView.as_view()),
    # 验证邮箱
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    # 地址页面展示路由:
    url(r'^addresses/$', views.AddressView.as_view(), name='address'),

]