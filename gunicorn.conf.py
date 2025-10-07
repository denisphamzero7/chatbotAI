bind = '0.0.0.0:8080'
workers = 2
threads = 4
backlog = 512
chdir = '/www/wwwroot/apidieuhanhnoivu.danang.gov.vn/chatbotAI'
loglevel = 'info'
capture_output = True
preload_app = True

errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/access.log'
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s "%(f)s" "%(a)s"'
pidfile = chdir + '/logs/gunicorn.pid'
