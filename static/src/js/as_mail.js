odoo.define('mail_tracking.partner_tracking', function(require){
"use strict";

var $ = require('$');
var core = require('web.core');
var session = require('web.session');
var Model = require('web.Model');
var ActionManager = require('web.ActionManager');
var chat_manager = require('mail.chat_manager');
var ChatThread = require('mail.ChatThread');
var Chatter = require('mail.Chatter');

var _t = core._t;
var MessageModel = new Model('mail.message', session.context);


ChatThread.include({
    on_resend_message_click: function (event) {
        //var partner_id = $(event.currentTarget).data('partner');
        //var state = {
        //    'model': 'res.partner',
        //    'id': partner_id,
        //    'title': _t("Tracking partner"),
        //};
        event.preventDefault();
	console.log('Clickeo re-send');
        var message_id = $(event.currentTarget).data('message-id');
	console.log(message_id);

	MessageModel.call('resend', [message_id]).then(function (result) {
		    // do something with change_password result
			console.log('Envio el mensaje');
	});

	// console.log(event);
        //this.action_manager.do_push_state(state);
        //var action = {
        //    type:'ir.actions.act_window',
        //    view_type: 'form',
        //    view_mode: 'form',
        //    res_model: 'res.partner',
        //    views: [[false, 'form']],
        //    target: 'current',
        //    res_id: partner_id,
        //};
        //this.do_action(action);
    },
    bind_events_as_mail: function () {
        this.$el.on('click', '.o_resend_message',
                    this.on_resend_message_click);
    },
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.action_manager = this.findAncestor(function(ancestor){
            return ancestor instanceof ActionManager;
        });
    },
    start: function () {
        this._super();
        this.bind_events_as_mail();
    },
});

}); // odoo.define
