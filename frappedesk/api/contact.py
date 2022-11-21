import frappe

@frappe.whitelist()
def get_contact_email():
    contact_email = frappe.db.get_list("Contact", ["email_id"], pluck="email_id")
    return contact_email

@frappe.whitelist()
def get_contact_organization():
    contact_organization = frappe.db.get_list("Contact", ["organization"], pluck="organization")
    return contact_organization