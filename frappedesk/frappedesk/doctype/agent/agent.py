# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Agent(Document):
	def before_save(self):
		if self.name != self.user:
			self.name = self.user
			self.set_user_roles()

	def set_user_roles(self):
		user = frappe.get_doc("User", self.user)
		for role in ["Agent", "System Manager"]:
			user.append("roles", {"role": role})
		user.save()

	def on_update(self):
		if self.has_value_changed("is_active"):
			if not self.is_active:
				self.remove_from_support_rotations()
			else:
				self.add_to_support_rotations()

		if self.has_value_changed("groups") and self.is_active:
			previous = self.get_doc_before_save()
			if previous:
				for group in previous.groups:
					if not next((g for g in self.groups if g.agent_group == group.agent_group), None):
						self.remove_from_support_rotations(group.agent_group)

			self.add_to_support_rotations()

	def on_trash(self):
		self.remove_from_support_rotations()

	def add_to_support_rotations(self, group=None):
		"""Add the agent to the support rotation for the given group or all groups the agent belongs to
		if agent already added to the support roatation for a group, skip

		:param str group: Agent Group name, defaults to None.
		"""

		rule_docs = []
		if not group:
			# Add the agent to the base support rotation

			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule",
					frappe.get_doc("Frappe Desk Settings").get_base_support_rotation(),
				)
			)

			# Add the agent to the support rotation for each group they belong to
			if self.groups:
				for group in self.groups:
					try:
						agent_group_assignment_rule = frappe.get_doc(
							"Agent Group", group.agent_group
						).get_assignment_rule()
						rule_docs.append(frappe.get_doc("Assignment Rule", agent_group_assignment_rule,))
					except frappe.DoesNotExistError:
						frappe.throw(
							frappe._("Assignment Rule for Agent Group {0} does not exist").format(
								group.agent_group
							)
						)
		else:
			# check if the group is in self.groups
			if next((group for group in self.groups if group["group_name"] == group), None):
				rule_docs.append(
					frappe.get_doc(
						"Assignment Rule", frappe.get_doc("Agent Group", group).get_assignment_rule(),
					)
				)
			else:
				frappe.throw(
					frappe._("Agent {0} does not belong to group {1}".format(self.agent_name, group))
				)

		for rule_doc in rule_docs:
			skip = False
			if rule_doc:
				if rule_doc.users and len(rule_doc.users) > 0:
					for user in rule_doc.users:
						if user.user == self.user:  # if the user is already in the rule, skip
							skip = True
							break
				if skip:
					continue

				user_doc = frappe.get_doc({"doctype": "Assignment Rule User", "user": self.user})
				rule_doc.append("users", user_doc)
				rule_doc.save(ignore_permissions=True)

	def remove_from_support_rotations(self, group=None):
		rule_docs = []

		if group:
			# remove the agent from the support rotation for the given group
			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule", frappe.get_doc("Agent Group", group).get_assignment_rule(),
				)
			)

		else:
			# Remove the agent from the base support rotation
			rule_docs.append(
				frappe.get_doc(
					"Assignment Rule",
					frappe.get_doc("Frappe Desk Settings").get_base_support_rotation(),
				)
			)

			# Remove the agent from the support rotation for each group they belong to
			for group in self.groups:
				rule_docs.append(
					frappe.get_doc(
						"Assignment Rule",
						frappe.get_doc("Agent Group", group.agent_group).get_assignment_rule(),
					)
				)

		for rule_doc in rule_docs:
			if rule_doc.users and len(rule_doc.users) > 0:
				for user in rule_doc.users:
					if user.user == self.user:
						rule_doc.remove(user)
						rule_doc.save()

	def in_group(self, group):
		"""Check if the agent is in the given group"""
		if self.groups:
			return next((g for g in self.groups if g.agent_group == group), False)
		return False


@frappe.whitelist()
def create_agent(first_name, last_name, email, signature, team):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"first_name": first_name,
				"last_name": last_name,
				"email": email,
				"email_signature": signature,
			}
		).insert()

		user.send_welcome_mail_to_user()

	return frappe.get_doc({"doctype": "Agent", "user": user.name, "group": team}).insert()
