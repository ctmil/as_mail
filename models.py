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

	sender_partner_id = fields.Many2one('res.partner',related='mail_message_id.author_id')
