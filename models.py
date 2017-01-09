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

	@api.one
	def compute_sender_partner_id(self):
		if self.sender:
			sender = self.sender
			position_start = sender.find('<')
			intermediate_sender = sender[position_start + 1]
			final_sender = intermediate_sender[:len(intermediate_sender)-1]
			partners = self.env['res.partner'].search([('email','=',final_sender)])
			if partners:
				self.sender_partner_id = partners[0].id

	#sender_partner_id = fields.Many2one('res.partner',related='mail_message_id.author_id')
	sender_partner_id = fields.Many2one('res.partner',related='mail_message_id.author_id')
