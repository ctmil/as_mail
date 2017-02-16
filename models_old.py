# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp import tools
import datetime

class fetchmail_server(osv.osv):
	_inherit = 'fetchmail.server'


	def fetch_mail_all(self, cr, uid, ids, context=None):
	        """WARNING: meant for cron usage only - will commit() after each email!"""
		import pdb;pdb.set_trace()
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
        	            imap_server.select()
			    date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")
			    # result, data = mail.uid('search', None, '(SENTSINCE {date})'.format(date=date))
                	    # result, data = imap_server.search(None, '(UNSEEN)')
                	    result, data = imap_server.search(None, '(SENTSINCE {date})'.format(date=date))
			    import pdb;pdb.set_trace()
	                    for num in data[0].split():
        	                res_id = None
                	        result, data = imap_server.fetch(num, '(RFC822)')
	                        imap_server.store(num, '-FLAGS', '\\Seen')
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
        	                imap_server.store(num, '+FLAGS', '\\Seen')
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
		'body': fields.text('Contenido')
		}

	_order  = 'mail_message_id desc, date desc'
	
	def init(self, cr):
        	tools.sql.drop_view_if_exists(cr, 'as_mail_message')
	        cr.execute("""
			create view as_mail_message as 
			select a.mail_message_id * a.res_partner_id as id,a.mail_message_id as mail_message_id,a.res_partner_id as res_partner_id,b.author_id as author_id,b.message_type as message_type, 
			b.subject as subject, b.email_from as email_from,b.date as date,b.body as body from mail_message_res_partner_rel a inner join mail_message b on a.mail_message_id = b.id
			where b.message_type in ('comment','email')
	        	""")
                                                 
