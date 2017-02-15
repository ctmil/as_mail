# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp import tools


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
		'date': fields.date('Fecha')
		}

	_order  = 'mail_message_id desc, date desc'
	
	def init(self, cr):
        	tools.sql.drop_view_if_exists(cr, 'as_mail_message')
	        cr.execute("""
			create view as_mail_message as 
			select a.mail_message_id as message_id,a.res_partner_id as res_partner_id,b.author_id as author_id,b.message_type as message_type, 
			b.subject as subject, b.email_from as email_from,b.date as date from mail_message_res_partner_rel a inner join mail_message b on a.mail_message_id = b.id
			where b.message_type in ('comment','email')
	        	""")
                                                 
