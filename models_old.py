# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import tools
import datetime
import logging
import poplib
import time
import email
from imaplib import IMAP4
from imaplib import IMAP4_SSL
from poplib import POP3
from poplib import POP3_SSL
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from openerp.osv import fields, osv
from openerp import tools, api, SUPERUSER_ID
from openerp.tools.translate import _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
poplib._MAXLINE = 65536


class mail_message(osv.osv):
	_inherit = 'mail.message'

	def resend(self, cr, uid, ids, context=None):
		print "Resend"
		message = self.pool.get('mail.message').browse(cr,uid,ids)
		if message:
			if message.partner_ids and message.subject \
				and message.model == 'purchase.order' or message.model == 'sale.order':
				res_id = message.res_id
				post_vars = {
						'subject': message.subject, 
						'body': message.body, 
						'partner_ids': message.partner_ids.ids,
						'attachment_ids': message.attachment_ids.ids
						}

				obj = self.pool.get(message.model).browse(cr,uid,res_id)
				if obj:
					res = self.pool.get(message.model).message_post(cr,uid,res_id,context={},**post_vars)

mail_message()

class fetchmail_server(osv.osv):
	_inherit = 'fetchmail.server'

	def _fetch_mails_all(self, cr, uid, ids=False, context=None):
	        if not ids:
	            ids = self.search(cr, uid, [('state','=','done'),('type','in',['pop','imap'])])
                return self.fetch_mail_all(cr, uid, ids, context=context)


	def fetch_mail_all(self, cr, uid, ids, context=None):
	        """WARNING: meant for cron usage only - will commit() after each email!"""
        	context = dict(context or {})
	        context['fetchmail_cron_running'] = True
        	mail_thread = self.pool.get('mail.thread')
	        action_pool = self.pool.get('ir.actions.server')
        	for server in self.browse(cr, uid, ids, context=context):
	            _logger.info('start checking for new emails on %s server %s', server.type, server.name)
        	    context.update({'fetchmail_server_id': server.id, 'server_type': server.type})
	            count, failed = 0, 0
        	    imap_server = False
	            pop_server = False
        	    if server.type == 'imap':
                	try:
	                    imap_server = server.connect()
        	            imap_server.select("INBOX")
			    #date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
			    date = (datetime.date.today() - datetime.timedelta(30)).strftime("%d-%b-%Y")
                            date = date.replace('ene','Jan')
                            date = date.replace('feb','Feb')
                            date = date.replace('mar','Mar')
                            date = date.replace('abr','Apr')
                            date = date.replace('may','May')
                            date = date.replace('jun','Jun')
                            date = date.replace('jul','Jul')
                            date = date.replace('ago','Aug')
                            date = date.replace('sep','Sep')
                            date = date.replace('oct','Oct')
                            date = date.replace('nov','Nov')
                            date = date.replace('dic','Dec')

			    # result, data = mail.uid('search', None, '(SENTSINCE {date})'.format(date=date))
                	    # result, data = imap_server.search(None, '(UNSEEN)')
			    _logger.info('[DEBUG]')
			    _logger.info(date)
                	    result, data = imap_server.search(None, '(SENTSINCE {date})'.format(date=date))
                	    #result, data = imap_server.search(None, '(SINCE {date})'.format(date=date))
                	    #result, data = imap_server.search(None, '(SENTON {date})'.format(date=date))
	                    for num in data[0].split():
        	                res_id = None
                	        result, data = imap_server.fetch(num, '(RFC822)')
		                raw_email = data[0][1]
                		email_message = email.message_from_string(raw_email)
				message_id = email_message['Message-ID']
				mail_message_id = self.pool.get('mail.message').search(cr,uid,[('message_id','=',message_id)])
				if not mail_message_id:
		                        #imap_server.store(num, '-FLAGS', '\\Seen')
        		                try:
                		            res_id = mail_thread.message_process(cr, uid, server.object_id.model,
                        	                                         data[0][1],
                                	                                 save_original=server.original,
                                        	                         strip_attachments=(not server.attach),
                                                	                 context=context)
	                	        except Exception:
        	                	    _logger.info('Failed to process mail from %s server %s.', server.type, server.name, exc_info=True)
	                	            failed += 1
        	                	if res_id and server.action_id:
	        	                    action_pool.run(cr, uid, [server.action_id.id], {'active_id': res_id, 'active_ids': [res_id], 'active_model': context.get("thread_model", server.object_id.model)})
        	                # imap_server.store(num, '+FLAGS', '\\Seen')
                		        cr.commit()
	                        count += 1
        	            _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.type, server.name, (count - failed), failed)
                	except Exception:
	                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type, server.name, exc_info=True)
        	        finally:
                	    if imap_server:
	                        imap_server.close()
        	                imap_server.logout()
	            elif server.type == 'pop':
        	        try:
                	    while True:
	                        pop_server = server.connect()
        	                (numMsgs, totalSize) = pop_server.stat()
                	        pop_server.list()
                        	for num in range(1, min(MAX_POP_MESSAGES, numMsgs) + 1):
	                            (header, msges, octets) = pop_server.retr(num)
        	                    msg = '\n'.join(msges)
                	            res_id = None
                        	    try:
                                	res_id = mail_thread.message_process(cr, uid, server.object_id.model,
                                                                     msg,
                                                                     save_original=server.original,
                                                                     strip_attachments=(not server.attach),
                                                                     context=context)
	                                pop_server.dele(num)
        	                    except Exception:
                	                _logger.info('Failed to process mail from %s server %s.', server.type, server.name, exc_info=True)
                        	        failed += 1
	                            if res_id and server.action_id:
        	                        action_pool.run(cr, uid, [server.action_id.id], {'active_id': res_id, 'active_ids': [res_id], 'active_model': context.get("thread_model", server.object_id.model)})
                	            cr.commit()
	                        if numMsgs < MAX_POP_MESSAGES:
        	                    break
                	        pop_server.quit()
                        	_logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", numMsgs, server.type, server.name, (numMsgs - failed), failed)
	                except Exception:
        	            _logger.info("General failure when trying to fetch mail from %s server %s.", server.type, server.name, exc_info=True)
                	finally:
	                    if pop_server:
        	                pop_server.quit()
	            server.write({'date': time.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)})
	        return True

class as_mail_message(osv.osv):
	_name = "as.mail.message"
	_description = "AS Mail Message"
	_auto = False

	_columns = {
		'mail_message_id': fields.many2one('mail.message','Mensaje'),
		'res_partner_id': fields.many2one('res.partner','Destinatario'),
		'author_id': fields.many2one('res.partner','Autor'),
		'message_type': fields.char('Tipo de mensaje'),
		'subject': fields.char('Asunto'),
		'email_from': fields.char('Desde'),
		'date': fields.date('Fecha'),
		'body': fields.text('Contenido'),
		'model': fields.char('Modelo'),
		'res_id': fields.integer('Res ID'),
		'state_email': fields.char('Estado e-mail'),
		}

	_order  = 'mail_message_id desc, date desc'
	
	def init(self, cr):
        	tools.sql.drop_view_if_exists(cr, 'as_mail_message')
	        cr.execute("""
			create view as_mail_message as 
			select a.mail_message_id * a.res_partner_id as id,a.mail_message_id as mail_message_id,a.res_partner_id as res_partner_id,b.author_id as author_id,b.message_type as message_type, 
			b.subject as subject, b.email_from as email_from,b.date as date,b.body as body,b.model as model,b.res_id as res_id,c.state as state_email
			from mail_message_res_partner_rel a inner join mail_message b on a.mail_message_id = b.id
			left join mail_tracking_email c on a.mail_message_id = c.mail_message_id
			where b.message_type in ('comment','email')
			union
			select a.mail_message_id * a.res_partner_id as id,a.mail_message_id as mail_message_id,a.res_partner_id as res_partner_id,b.author_id as author_id,b.message_type as message_type, 
			b.subject as subject, b.email_from as email_from,b.date as date,b.body as body,b.model as model,b.res_id as res_id,c.state as state_email
			from mail_message_res_partner_starred_rel a inner join mail_message b on a.mail_message_id = b.id
			left join mail_tracking_email c on a.mail_message_id = c.mail_message_id
			where b.message_type in ('comment','email')
			union
			select a.id * a.author_id as id,a.id as mail_message_id,b.author_id as res_partner_id,a.author_id as author_id,a.message_type as message_type, 
			a.subject as subject, a.email_from as email_from,a.date as date,a.body as body,b.model as model,b.res_id as res_id,c.state as state_email
			from mail_message a inner join mail_message b on a.parent_id = b.id 
			left join mail_tracking_email c on a.id = c.mail_message_id
			where a.message_type in ('comment','email') 
			and a.id not in (select mail_message_id from mail_message_res_partner_rel) 
			and a.id not in (select mail_message_id from mail_message_res_partner_starred_rel)
	        	""")
                                                 
