# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
from openerp.fields import Date as newdate

#Get the logger
_logger = logging.getLogger(__name__)

class mail_tracking_email(models.Model):
        _inherit = 'mail.tracking.email'

        #@api.one
        #def _compute_sender_partner_id(self):
        #@api.one
        #@api.onchange('sender')
        @api.model
        #def _compute_sender_partner_id(self):
        def create(self, vals):
                if 'sender' in vals.keys():
                        #import pdb;pdb.set_trace()
                        sender = vals['sender']
                        position_start = sender.find('<')
                        intermediate_sender = sender[position_start + 1:]
                        final_sender = intermediate_sender[:len(intermediate_sender)-1]
                        partners = self.env['res.partner'].search([('email','=',final_sender)])
                        if partners:
                                vals['sender_partner_id'] = partners[0].id
                return super(mail_tracking_email, self).create(vals)

        sender_partner_id = fields.Many2one('res.partner',related='mail_message_id.author_id')


class mail_message(models.Model):
        _inherit = 'mail.message'
	_order = 'id desc'

	"""	
	@api.model
	def message_fetch(self, domain, limit=20):
		new_domain = []
		constraints = ['create_date','needaction']
		for  idx_domain in domain:
			if idx_domain[0] not in constraints:
				new_domain.append(idx_domain)
		resultados = None
		if new_domain == [] or new_domain[0] == ('channel_id','in',[]):
			uid  = self.env.context['uid']
			user = self.env['res.users'].browse(uid)
			partner_id = user.partner_id.id
			new_domain = [('author_id','=',partner_id)]
			resultados = self.search(new_domain, limit=limit).message_format()
			index = 0
			for resultado in resultados:
				channel = resultado.get('channel_id',None)
				if not channel:
					resultados[index]['channel_id'] = [3]
				index = index + 1
		new_domain.append(('message_type','=','comment'))
		if not resultados:
			return self.search(new_domain,limit=limit).message_format()
		else:
			return resultados
	"""

        @api.one
        def _compute_mail_owner(self):
                #if self.id == 25652:
                #       import pdb;pdb.set_trace()
                return_value = False
                uid = self.env.context['uid']
                user_uid = self.env['res.users'].browse(uid)
                partner_uid = user_uid.partner_id.id
                if self.author_id.id == user_uid.partner_id.id:
                        return_value = True
                else:
                        if partner_uid in self.partner_ids.ids:
                                return_value = True
                self.mail_owner = return_value

        @api.one
        def _compute_partner_ids_char_v3(self):
                if self.partner_ids:
                        #import pdb;pdb.set_trace()
                        partner_ids_ids = [str(c) for c in self.partner_ids.ids]
                        return_value = ','.join(partner_ids_ids)
                        self.partner_ids_char_v3 = return_value

        @api.one
        def _compute_original_author_id(self):
                if self.parent_id:
                        self.original_author_id = self.parent_id.author_id.id

        partner_ids_char_v3 = fields.Char('Partners Char',compute=_compute_partner_ids_char_v3)
        mail_owner = fields.Boolean('Mail Owner',compute=_compute_mail_owner)
        original_author_id = fields.Many2one('res.partner',string='Original Author',compute=_compute_original_author_id,store=True)
