# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json
from typing import Literal

import frappe
import frappe.utils
from frappe import _, qb
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html
from datetime import datetime

from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
	unlink_inter_company_doc,
	update_linked_doc,
	validate_inter_company_party,
)
from erpnext.accounts.party import get_party_account
from erpnext.controllers.selling_controller import SellingController
from erpnext.manufacturing.doctype.blanket_order.blanket_order import (
	validate_against_blanket_order,
)
from erpnext.manufacturing.doctype.production_plan.production_plan import (
	get_items_for_material_requests,
)
from erpnext.selling.doctype.customer.customer import check_credit_limit
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
	get_sre_reserved_qty_details_for_voucher,
	has_reserved_stock,
)
from erpnext.stock.get_item_details import get_default_bom, get_price_list_rate
from erpnext.stock.stock_balance import get_reserved_qty, update_bin_qty

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class WarehouseRequired(frappe.ValidationError):
	pass


class SalesOrder(SellingController):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.payment_schedule.payment_schedule import PaymentSchedule
		from erpnext.accounts.doctype.pricing_rule_detail.pricing_rule_detail import PricingRuleDetail
		from erpnext.accounts.doctype.sales_taxes_and_charges.sales_taxes_and_charges import SalesTaxesandCharges
		from erpnext.selling.doctype.sales_order_item.sales_order_item import SalesOrderItem
		from erpnext.selling.doctype.sales_team.sales_team import SalesTeam
		from erpnext.stock.doctype.packed_item.packed_item import PackedItem
		from frappe.types import DF

		additional_discount_percentage: DF.Float
		address_display: DF.SmallText | None
		advance_paid: DF.Currency
		advance_payment_status: DF.Literal["Not Requested", "Requested", "Partially Paid", "Fully Paid"]
		amended_from: DF.Link | None
		amount_eligible_for_commission: DF.Currency
		apply_discount_on: DF.Literal["", "Grand Total", "Net Total"]
		auto_repeat: DF.Link | None
		balance_amount: DF.Currency
		base_discount_amount: DF.Currency
		base_grand_total: DF.Currency
		base_in_words: DF.Data | None
		base_net_total: DF.Currency
		base_rounded_total: DF.Currency
		base_rounding_adjustment: DF.Currency
		base_total: DF.Currency
		base_total_taxes_and_charges: DF.Currency
		billing_status: DF.Literal["Not Billed", "Fully Billed", "Partly Billed", "Closed"]
		campaign: DF.Link | None
		commission_rate: DF.Float
		company: DF.Link
		company_address: DF.Link | None
		company_address_display: DF.SmallText | None
		contact_display: DF.SmallText | None
		contact_email: DF.Data | None
		contact_mobile: DF.SmallText | None
		contact_person: DF.Link | None
		contact_phone: DF.Data | None
		conversion_rate: DF.Float
		cost_center: DF.Link | None
		coupon_code: DF.Link | None
		created_by: DF.Link | None
		currency: DF.Link
		customer: DF.Link
		customer_address: DF.Link | None
		customer_group: DF.Link | None
		customer_name: DF.Data | None
		delivery_date: DF.Date | None
		delivery_status: DF.Literal["Not Delivered", "Fully Delivered", "Partly Delivered", "Closed", "Not Applicable"]
		disable_rounded_total: DF.Check
		discount_amount: DF.Currency
		dispatch_address: DF.SmallText | None
		dispatch_address_name: DF.Link | None
		dispatch_date: DF.Date | None
		end_date: DF.Date | None
		from_date: DF.Date | None
		grand_total: DF.Currency
		group_same_items: DF.Check
		ignore_pricing_rule: DF.Check
		in_words: DF.Data | None
		incoterm: DF.Link | None
		inter_company_order_reference: DF.Link | None
		is_internal_customer: DF.Check
		items: DF.Table[SalesOrderItem]
		language: DF.Data | None
		letter_head: DF.Link | None
		loyalty_amount: DF.Currency
		loyalty_points: DF.Int
		master_order_id: DF.Link | None
		named_place: DF.Data | None
		naming_series: DF.Literal["SAL-ORD-.YYYY.-"]
		net_total: DF.Currency
		order_type: DF.Literal["", "Sales", "Maintenance", "Shopping Cart", "Rental"]
		other_charges_calculation: DF.LongText | None
		outstanding_security_deposit_amount: DF.Currency
		overdue_status: DF.Literal["Active", "Overdue", "Renewed"]
		packed_items: DF.Table[PackedItem]
		paid_security_deposite_amount: DF.Currency
		party_account_currency: DF.Link | None
		payment_schedule: DF.Table[PaymentSchedule]
		payment_status: DF.Literal["Paid", "UnPaid", "Partially Paid"]
		payment_terms_template: DF.Link | None
		per_billed: DF.Percent
		per_delivered: DF.Percent
		per_picked: DF.Percent
		picked_up: DF.Datetime | None
		pickup_date: DF.Datetime | None
		pickup_reason: DF.Literal["", "Patient recovered", "Patient Expired", "Purchased Device from Us", "Purchased Device from Others", "Other Reason"]
		pickup_remark: DF.SmallText | None
		plc_conversion_rate: DF.Float
		po_date: DF.Date | None
		po_no: DF.Data | None
		previous_order_id: DF.Link | None
		price_list_currency: DF.Link
		pricing_rules: DF.Table[PricingRuleDetail]
		project: DF.Link | None
		refundable_security_deposit: DF.Currency
		rental_delivery_date: DF.Datetime | None
		represents_company: DF.Link | None
		reserve_stock: DF.Check
		rounded_total: DF.Currency
		rounding_adjustment: DF.Currency
		sales_partner: DF.Link | None
		sales_team: DF.Table[SalesTeam]
		security_deposit: DF.Data | None
		security_deposit_amount_return_to_client: DF.Currency
		security_deposit_status: DF.Literal["Unpaid", "Paid", "Partially Paid"]
		select_print_heading: DF.Link | None
		selling_price_list: DF.Link
		set_warehouse: DF.Link | None
		shipping_address: DF.SmallText | None
		shipping_address_name: DF.Link | None
		shipping_rule: DF.Link | None
		skip_delivery_note: DF.Check
		source: DF.Link | None
		start_date: DF.Date | None
		status: DF.Literal["Draft", "Pending", "Approved", "Rental Device Assigned", "Ready for Delivery", "DISPATCHED", "DELIVERED", "Active", "Ready for Pickup", "Picked Up", "Submitted to Office", "On Hold", "Overdue", "RENEWED", "To Pay", "To Deliver and Bill", "To Bill", "To Deliver", "Completed", "Cancelled", "Closed", "Partially Closed"]
		submitted_date: DF.Datetime | None
		tax_category: DF.Link | None
		tax_id: DF.Data | None
		taxes: DF.Table[SalesTaxesandCharges]
		taxes_and_charges: DF.Link | None
		tc_name: DF.Link | None
		technician_mobile_after_delivered: DF.Data | None
		technician_mobile_before_delivered: DF.Data | None
		technician_name_after_delivered: DF.Data | None
		technician_name_before_delivered: DF.Data | None
		terms: DF.TextEditor | None
		territory: DF.Link | None
		title: DF.Data | None
		to_date: DF.Date | None
		total: DF.Currency
		total_commission: DF.Currency
		total_net_weight: DF.Float
		total_no_of_dates: DF.Data | None
		total_qty: DF.Float
		total_taxes_and_charges: DF.Currency
		transaction_date: DF.Date
	# end: auto-generated types

	def __init__(self, *args, **kwargs):
		super(SalesOrder, self).__init__(*args, **kwargs)

	def onload(self) -> None:
		if frappe.db.get_single_value("Stock Settings", "enable_stock_reservation"):
			if self.has_unreserved_stock():
				self.set_onload("has_unreserved_stock", True)

		if has_reserved_stock(self.doctype, self.name):
			self.set_onload("has_reserved_stock", True)

	def validate(self):
		super(SalesOrder, self).validate()
		# self.validate_delivery_date()
		# self.validate_sales_order_payment_status(self)
		self.validate_proj_cust()
		self.validate_po()
		self.validate_uom_is_integer("stock_uom", "stock_qty")
		self.validate_uom_is_integer("uom", "qty")
		self.validate_for_items()
		self.validate_warehouse()
		self.validate_drop_ship()
		self.validate_reserved_stock()
		self.validate_serial_no_based_delivery()
		validate_against_blanket_order(self)
		validate_inter_company_party(
			self.doctype, self.customer, self.company, self.inter_company_order_reference
		)

		if self.coupon_code:
			from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code

			validate_coupon_code(self.coupon_code)

		from erpnext.stock.doctype.packed_item.packed_item import make_packing_list

		make_packing_list(self)

		# self.validate_with_previous_doc()
		# self.set_status()	

		if not self.billing_status:
			self.billing_status = "Not Billed"
		if not self.delivery_status:
			self.delivery_status = "Not Delivered"
		if not self.advance_payment_status:
			self.advance_payment_status = "Not Requested"

		self.reset_default_field_value("set_warehouse", "items", "warehouse")


	
	# def validate_sales_order_payment_status(self):
	# 	# Access the rounded_total and advance_paid fields from the document
	# 	rounded_total = self.rounded_total
	# 	advance_paid = self.advance_paid

	# 	# Check if the rounded_total is equal to advance_paid
	# 	if rounded_total == advance_paid:
	# 		# If rounded_total equals advance_paid, set payment_status to 'Paid'
	# 		self.payment_status = 'Paid'
	# 	elif advance_paid == 0:
	# 		# If advance_paid is zero, set payment_status to 'Unpaid'
	# 		self.payment_status = 'Unpaid'
	# 	else:
	# 		# If rounded_total is not equal to advance_paid and advance_paid is not zero,
	# 		# set payment_status to 'Partially Paid'
	# 		self.payment_status = 'Partially Paid'

	# 	# Save the changes to the selfument
	# 	doc.save()


	def validate_po(self):
		# validate p.o date v/s delivery date
		if self.po_date and not self.skip_delivery_note:
			for d in self.get("items"):
				if d.delivery_date and getdate(self.po_date) > getdate(d.delivery_date):
					frappe.throw(
						_("Row #{0}: Expected Delivery Date cannot be before Purchase Order Date").format(d.idx)
					)

		if self.po_no and self.customer and not self.skip_delivery_note:
			so = frappe.db.sql(
				"select name from `tabSales Order` \
				where ifnull(po_no, '') = %s and name != %s and docstatus < 2\
				and customer = %s",
				(self.po_no, self.name, self.customer),
			)
			if so and so[0][0]:
				if cint(
					frappe.db.get_single_value("Selling Settings", "allow_against_multiple_purchase_orders")
				):
					frappe.msgprint(
						_("Warning: Sales Order {0} already exists against Customer's Purchase Order {1}").format(
							frappe.bold(so[0][0]), frappe.bold(self.po_no)
						),
						alert=True,
					)
				else:
					frappe.throw(
						_(
							"Sales Order {0} already exists against Customer's Purchase Order {1}. To allow multiple Sales Orders, Enable {2} in {3}"
						).format(
							frappe.bold(so[0][0]),
							frappe.bold(self.po_no),
							frappe.bold(_("'Allow Multiple Sales Orders Against a Customer's Purchase Order'")),
							get_link_to_form("Selling Settings", "Selling Settings"),
						)
					)

	def validate_for_items(self):
		for d in self.get("items"):

			# used for production plan
			d.transaction_date = self.transaction_date

			tot_avail_qty = frappe.db.sql(
				"select projected_qty from `tabBin` \
				where item_code = %s and warehouse = %s",
				(d.item_code, d.warehouse),
			)
			d.projected_qty = tot_avail_qty and flt(tot_avail_qty[0][0]) or 0

	def product_bundle_has_stock_item(self, product_bundle):
		"""Returns true if product bundle has stock item"""
		ret = len(
			frappe.db.sql(
				"""select i.name from tabItem i, `tabProduct Bundle Item` pbi
			where pbi.parent = %s and pbi.item_code = i.name and i.is_stock_item = 1""",
				product_bundle,
			)
		)
		return ret

	def validate_sales_mntc_quotation(self):
		for d in self.get("items"):
			if d.prevdoc_docname:
				res = frappe.db.sql(
					"select name from `tabQuotation` where name=%s and order_type = %s",
					(d.prevdoc_docname, self.order_type),
				)
				if not res:
					frappe.msgprint(_("Quotation {0} not of type {1}").format(d.prevdoc_docname, self.order_type))

	def validate_delivery_date(self):
		if self.order_type == "Sales" and not self.skip_delivery_note:
			delivery_date_list = [d.delivery_date for d in self.get("items") if d.delivery_date]
			max_delivery_date = max(delivery_date_list) if delivery_date_list else None
			if (max_delivery_date and not self.delivery_date) or (
				max_delivery_date and getdate(self.delivery_date) != getdate(max_delivery_date)
			):
				self.delivery_date = max_delivery_date
			if self.delivery_date:
				for d in self.get("items"):
					if not d.delivery_date:
						d.delivery_date = self.delivery_date
					if getdate(self.transaction_date) > getdate(d.delivery_date):
						frappe.msgprint(
							_("Expected Delivery Date should be after Sales Order Date"),
							indicator="orange",
							title=_("Invalid Delivery Date"),
							raise_exception=True,
						)
			else:
				frappe.throw(_("Please enter Delivery Date"))

		self.validate_sales_mntc_quotation()

	def validate_proj_cust(self):
		if self.project and self.customer_name:
			res = frappe.db.sql(
				"""select name from `tabProject` where name = %s
				and (customer = %s or ifnull(customer,'')='')""",
				(self.project, self.customer),
			)
			if not res:
				frappe.throw(
					_("Customer {0} does not belong to project {1}").format(self.customer, self.project)
				)

	def validate_warehouse(self):
		super(SalesOrder, self).validate_warehouse()

		for d in self.get("items"):
			if (
				(
					frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1
					or (self.has_product_bundle(d.item_code) and self.product_bundle_has_stock_item(d.item_code))
				)
				and not d.warehouse
				and not cint(d.delivered_by_supplier)
			):
				frappe.throw(
					_("Delivery warehouse required for stock item {0}").format(d.item_code), WarehouseRequired
				)

	def validate_with_previous_doc(self):
		super(SalesOrder, self).validate_with_previous_doc(
			{
				"Quotation": {"ref_dn_field": "prevdoc_docname", "compare_fields": [["company", "="]]},
				"Quotation Item": {
					"ref_dn_field": "quotation_item",
					"compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
					"is_child_table": True,
					"allow_duplicate_prev_row_id": True,
				},
			}
		)

		if cint(frappe.db.get_single_value("Selling Settings", "maintain_same_sales_rate")):
			self.validate_rate_with_reference_doc([["Quotation", "prevdoc_docname", "quotation_item"]])

	def update_enquiry_status(self, prevdoc, flag):
		enq = frappe.db.sql(
			"select t2.prevdoc_docname from `tabQuotation` t1, `tabQuotation Item` t2 where t2.parent = t1.name and t1.name=%s",
			prevdoc,
		)
		if enq:
			frappe.db.sql("update `tabOpportunity` set status = %s where name=%s", (flag, enq[0][0]))

	def update_prevdoc_status(self, flag=None):
		for quotation in set(d.prevdoc_docname for d in self.get("items")):
			if quotation:
				doc = frappe.get_doc("Quotation", quotation)
				if doc.docstatus.is_cancelled():
					frappe.throw(_("Quotation {0} is cancelled").format(quotation))

				# doc.set_status(update=True)
				doc.update_opportunity("Converted" if flag == "submit" else "Quotation")

	def validate_drop_ship(self):
		for d in self.get("items"):
			if d.delivered_by_supplier and not d.supplier:
				frappe.throw(_("Row #{0}: Set Supplier for item {1}").format(d.idx, d.item_code))

	def on_submit(self):
		self.check_credit_limit()
		self.update_reserved_qty()
		if self.order_type == 'Rental' and self.security_deposit and float(self.security_deposit) > 0:
			self.create_security_deposit_journal_entry()
		frappe.get_doc("Authorization Control").validate_approving_authority(
			self.doctype, self.company, self.base_grand_total, self
		)
		self.update_project()
		# self.update_prevdoc_status("submit")

		self.update_blanket_order()

		update_linked_doc(self.doctype, self.name, self.inter_company_order_reference)
		if self.coupon_code:
			from erpnext.accounts.doctype.pricing_rule.utils import update_coupon_code_count

			update_coupon_code_count(self.coupon_code, "used")

		if self.get("reserve_stock"):
			self.create_stock_reservation_entries()
		self.update_sales_order_status()

	def create_security_deposit_journal_entry(self):
		try:
			# sales_order = frappe.get_doc("Sales Order", self.name)

			# Create a new Journal Entry document
			journal_entry = frappe.new_doc("Journal Entry")
			journal_entry.sales_order_id = self.name
			journal_entry.master_order_id = self.master_order_id
			journal_entry.journal_entry_type = "Security Deposit"
			journal_entry.journal_entry = "Journal Entry"
			journal_entry.posting_date = frappe.utils.nowdate()
			journal_entry.security_deposite_type = "Booking as Advance From Client"


			# Add accounts for debit and credit
			journal_entry.append("accounts", {
				"account": "Debtors - INR",
				"party_type": "Customer",
				"party": self.customer,
				"debit_in_account_currency": self.security_deposit
			})
			journal_entry.append("accounts", {
				"account": "Rental Order Security Deposit Receivable - INR",
				"party_type": "Customer",
				"party": self.customer,
				"credit_in_account_currency": self.security_deposit
			})

			# Save the Journal Entry document
			journal_entry.insert()
			journal_entry.submit()

			frappe.msgprint("Security Deposit Journal Entry created successfully")  # Debug message

			return True
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), _("Failed to create Security Deposit Journal Entry"))
			frappe.throw(_("Failed to create Security Deposit Journal Entry. Please try again later."))



	def before_submit(self):
		if self.previous_order_id:
			overlap = check_overlap(self)
			if overlap:
				frappe.throw("Current start and end dates overlap with the previous order.")	

	def update_sales_order_status(self):
		if self.previous_order_id:
			# Update status in parent Sales Order
			existing_orders = frappe.get_list("Sales Order", filters={"name": self.previous_order_id})
			for order in existing_orders:
				sales_order = frappe.get_doc("Sales Order", order.name)
				sales_order.status = "RENEWED"
				sales_order.save()

			# Update status in child table (Sales Order Item)
			child_table = frappe.get_all("Sales Order Item", filters={"parent": self.previous_order_id})
			for order_item in child_table:
				sales_order_item = frappe.get_doc("Sales Order Item", order_item.name)
				sales_order_item.child_status = "Renewed"
				sales_order_item.save()
		# elif self.order_type == "Rental":
		# 	# Update master_order_id with the current doc name
		# 	self.master_order_id = self.name
		# 	self.save()
		# self.save()
	



	def on_cancel(self):
		self.item_status_change_cancel()

		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		super(SalesOrder, self).on_cancel()

		# Cannot cancel closed SO
		if self.status == "Closed":
			frappe.throw(_("Closed order cannot be cancelled. Unclose to cancel."))

		# self.check_nextdoc_docstatus()
		self.update_reserved_qty()
		self.update_project()
		self.update_prevdoc_status("cancel")

		self.db_set("status", "Cancelled")

		self.update_blanket_order()
		self.cancel_stock_reservation_entries()

		unlink_inter_company_doc(self.doctype, self.name, self.inter_company_order_reference)
		if self.coupon_code:
			from erpnext.accounts.doctype.pricing_rule.utils import update_coupon_code_count

			update_coupon_code_count(self.coupon_code, "cancelled")


	def item_status_change_cancel(self):
		for item in self.get("items"):
			item_code = item.item_code
			item_doc = frappe.get_doc("Item", item_code)
			if item_doc.status == "Rented Out":
				item_doc.status = "Available"
				item_doc.save()

		frappe.db.commit()

	def on_trash(self):
		# pass
		self.item_status_change_cancel()

	def update_project(self):
		if (
			frappe.db.get_single_value("Selling Settings", "sales_update_frequency") != "Each Transaction"
		):
			return

		if self.project:
			project = frappe.get_doc("Project", self.project)
			project.update_sales_amount()
			project.db_update()

	def check_credit_limit(self):
		# if bypass credit limit check is set to true (1) at sales order level,
		# then we need not to check credit limit and vise versa
		if not cint(
			frappe.db.get_value(
				"Customer Credit Limit",
				{"parent": self.customer, "parenttype": "Customer", "company": self.company},
				"bypass_credit_limit_check",
			)
		):
			check_credit_limit(self.customer, self.company)

	def check_nextdoc_docstatus(self):
		linked_invoices = frappe.db.sql_list(
			"""select distinct t1.name
			from `tabSales Invoice` t1,`tabSales Invoice Item` t2
			where t1.name = t2.parent and t2.sales_order = %s and t1.docstatus = 0""",
			self.name,
		)

		if linked_invoices:
			linked_invoices = [get_link_to_form("Sales Invoice", si) for si in linked_invoices]
			frappe.throw(
				_("Sales Invoice {0} must be deleted before cancelling this Sales Order").format(
					", ".join(linked_invoices)
				)
			)

	def check_modified_date(self):
		mod_db = frappe.db.get_value("Sales Order", self.name, "modified")
		date_diff = frappe.db.sql("select TIMEDIFF('%s', '%s')" % (mod_db, cstr(self.modified)))
		if date_diff and date_diff[0][0]:
			frappe.throw(_("{0} {1} has been modified. Please refresh.").format(self.doctype, self.name))

	def update_status(self, status):
		self.check_modified_date()
		# self.set_status(update=True, status=status)
		self.update_reserved_qty()
		self.notify_update()
		clear_doctype_notifications(self)

	def update_reserved_qty(self, so_item_rows=None):
		"""update requested qty (before ordered_qty is updated)"""
		item_wh_list = []

		def _valid_for_reserve(item_code, warehouse):
			if (
				item_code
				and warehouse
				and [item_code, warehouse] not in item_wh_list
				and frappe.get_cached_value("Item", item_code, "is_stock_item")
			):
				item_wh_list.append([item_code, warehouse])

		for d in self.get("items"):
			if (not so_item_rows or d.name in so_item_rows) and not d.delivered_by_supplier:
				if self.has_product_bundle(d.item_code):
					for p in self.get("packed_items"):
						if p.parent_detail_docname == d.name and p.parent_item == d.item_code:
							_valid_for_reserve(p.item_code, p.warehouse)
				else:
					_valid_for_reserve(d.item_code, d.warehouse)

		for item_code, warehouse in item_wh_list:
			update_bin_qty(item_code, warehouse, {"reserved_qty": get_reserved_qty(item_code, warehouse)})

	def on_update(self):
		pass

	def on_update_after_submit(self):
		# self.validate_sales_order_payment_status()
		self.check_credit_limit()

	def before_update_after_submit(self):
		# self.validate_sales_order_payment_status()
		self.validate_po()
		self.validate_drop_ship()
		self.validate_supplier_after_submit()
		# self.validate_delivery_date()

	def validate_supplier_after_submit(self):
		"""Check that supplier is the same after submit if PO is already made"""
		exc_list = []

		for item in self.items:
			if item.supplier:
				supplier = frappe.db.get_value(
					"Sales Order Item", {"parent": self.name, "item_code": item.item_code}, "supplier"
				)
				if item.ordered_qty > 0.0 and item.supplier != supplier:
					exc_list.append(
						_("Row #{0}: Not allowed to change Supplier as Purchase Order already exists").format(
							item.idx
						)
					)

		if exc_list:
			frappe.throw("\n".join(exc_list))

	def update_delivery_status(self):
		"""Update delivery status from Purchase Order for drop shipping"""
		tot_qty, delivered_qty = 0.0, 0.0

		for item in self.items:
			if item.delivered_by_supplier:
				item_delivered_qty = frappe.db.sql(
					"""select sum(qty)
					from `tabPurchase Order Item` poi, `tabPurchase Order` po
					where poi.sales_order_item = %s
						and poi.item_code = %s
						and poi.parent = po.name
						and po.docstatus = 1
						and po.status = 'Delivered'""",
					(item.name, item.item_code),
				)

				item_delivered_qty = item_delivered_qty[0][0] if item_delivered_qty else 0
				item.db_set("delivered_qty", flt(item_delivered_qty), update_modified=False)

			delivered_qty += item.delivered_qty
			tot_qty += item.qty

		if tot_qty != 0:
			self.db_set("per_delivered", flt(delivered_qty / tot_qty) * 100, update_modified=False)

	def update_picking_status(self):
		total_picked_qty = 0.0
		total_qty = 0.0
		per_picked = 0.0

		for so_item in self.items:
			if cint(
				frappe.get_cached_value("Item", so_item.item_code, "is_stock_item")
			) or self.has_product_bundle(so_item.item_code):
				total_picked_qty += flt(so_item.picked_qty)
				total_qty += flt(so_item.stock_qty)

		if total_picked_qty and total_qty:
			per_picked = total_picked_qty / total_qty * 100

		self.db_set("per_picked", flt(per_picked), update_modified=False)

	def set_indicator(self):
		"""Set indicator for portal"""
		self.indicator_color = {
			"Draft": "red",
			"On Hold": "orange",
			"To Deliver and Bill": "orange",
			"To Bill": "orange",
			"To Deliver": "orange",
			"Completed": "green",
			"Cancelled": "red",
		}.get(self.status, "blue")

		self.indicator_title = _(self.status)

	def on_recurring(self, reference_doc, auto_repeat_doc):
		def _get_delivery_date(ref_doc_delivery_date, red_doc_transaction_date, transaction_date):
			delivery_date = auto_repeat_doc.get_next_schedule_date(schedule_date=ref_doc_delivery_date)

			if delivery_date <= transaction_date:
				delivery_date_diff = frappe.utils.date_diff(ref_doc_delivery_date, red_doc_transaction_date)
				delivery_date = frappe.utils.add_days(transaction_date, delivery_date_diff)

			return delivery_date

		self.set(
			"delivery_date",
			_get_delivery_date(
				reference_doc.delivery_date, reference_doc.transaction_date, self.transaction_date
			),
		)

		for d in self.get("items"):
			reference_delivery_date = frappe.db.get_value(
				"Sales Order Item",
				{"parent": reference_doc.name, "item_code": d.item_code, "idx": d.idx},
				"delivery_date",
			)

			d.set(
				"delivery_date",
				_get_delivery_date(
					reference_delivery_date, reference_doc.transaction_date, self.transaction_date
				),
			)

	def validate_serial_no_based_delivery(self):
		reserved_items = []
		normal_items = []
		for item in self.items:
			if item.ensure_delivery_based_on_produced_serial_no:
				if item.item_code in normal_items:
					frappe.throw(
						_(
							"Cannot ensure delivery by Serial No as Item {0} is added with and without Ensure Delivery by Serial No."
						).format(item.item_code)
					)
				if item.item_code not in reserved_items:
					if not frappe.get_cached_value("Item", item.item_code, "has_serial_no"):
						frappe.throw(
							_(
								"Item {0} has no Serial No. Only serialized items can have delivery based on Serial No"
							).format(item.item_code)
						)
					if not frappe.db.exists("BOM", {"item": item.item_code, "is_active": 1}):
						frappe.throw(
							_("No active BOM found for item {0}. Delivery by Serial No cannot be ensured").format(
								item.item_code
							)
						)
				reserved_items.append(item.item_code)
			else:
				normal_items.append(item.item_code)

			if not item.ensure_delivery_based_on_produced_serial_no and item.item_code in reserved_items:
				frappe.throw(
					_(
						"Cannot ensure delivery by Serial No as Item {0} is added with and without Ensure Delivery by Serial No."
					).format(item.item_code)
				)

	def validate_reserved_stock(self):
		"""Clean reserved stock flag for non-stock Item"""

		enable_stock_reservation = frappe.db.get_single_value(
			"Stock Settings", "enable_stock_reservation"
		)

		for item in self.items:
			if item.reserve_stock and (not enable_stock_reservation or not cint(item.is_stock_item)):
				item.reserve_stock = 0

	def has_unreserved_stock(self) -> bool:
		"""Returns True if there is any unreserved item in the Sales Order."""

		reserved_qty_details = get_sre_reserved_qty_details_for_voucher("Sales Order", self.name)

		for item in self.get("items"):
			if not item.get("reserve_stock"):
				continue

			unreserved_qty = get_unreserved_qty(item, reserved_qty_details)
			if unreserved_qty > 0:
				return True

		return False

	@frappe.whitelist()
	def create_stock_reservation_entries(
		self,
		items_details: list[dict] = None,
		from_voucher_type: Literal["Pick List", "Purchase Receipt"] = None,
		notify=True,
	) -> None:
		"""Creates Stock Reservation Entries for Sales Order Items."""

		from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
			create_stock_reservation_entries_for_so_items as create_stock_reservation_entries,
		)

		create_stock_reservation_entries(
			sales_order=self,
			items_details=items_details,
			from_voucher_type=from_voucher_type,
			notify=notify,
		)

	@frappe.whitelist()
	def cancel_stock_reservation_entries(self, sre_list=None, notify=True) -> None:
		"""Cancel Stock Reservation Entries for Sales Order Items."""

		from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
			cancel_stock_reservation_entries,
		)

		cancel_stock_reservation_entries(
			voucher_type=self.doctype, voucher_no=self.name, sre_list=sre_list, notify=notify
		)


def get_unreserved_qty(item: object, reserved_qty_details: dict) -> float:
	"""Returns the unreserved quantity for the Sales Order Item."""

	existing_reserved_qty = reserved_qty_details.get(item.name, 0)
	return (
		item.stock_qty
		- flt(item.delivered_qty) * item.get("conversion_factor", 1)
		- existing_reserved_qty
	)


def get_list_context(context=None):
	from erpnext.controllers.website_list_for_contact import get_list_context

	list_context = get_list_context(context)
	list_context.update(
		{
			"show_sidebar": True,
			"show_search": True,
			"no_breadcrumbs": True,
			"title": _("Orders"),
		}
	)

	return list_context


@frappe.whitelist()
def close_or_unclose_sales_orders(names, status):
	if not frappe.has_permission("Sales Order", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = json.loads(names)
	for name in names:
		so = frappe.get_doc("Sales Order", name)
		if so.docstatus == 1:
			if status == "Closed":
				if so.status not in ("Cancelled", "Closed") and (
					so.per_delivered < 100 or so.per_billed < 100
				):
					so.update_status(status)
			else:
				if so.status == "Closed":
					so.update_status("Draft")
			so.update_blanket_order()

	frappe.local.message_log = []


def get_requested_item_qty(sales_order):
	result = {}
	for d in frappe.db.get_all(
		"Material Request Item",
		filters={"docstatus": 1, "sales_order": sales_order},
		fields=["sales_order_item", "sum(qty) as qty", "sum(received_qty) as received_qty"],
		group_by="sales_order_item",
	):
		result[d.sales_order_item] = frappe._dict({"qty": d.qty, "received_qty": d.received_qty})

	return result


@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
	requested_item_qty = get_requested_item_qty(source_name)

	def get_remaining_qty(so_item):
		return flt(
			flt(so_item.qty)
			- flt(requested_item_qty.get(so_item.name, {}).get("qty"))
			- max(
				flt(so_item.get("delivered_qty"))
				- flt(requested_item_qty.get(so_item.name, {}).get("received_qty")),
				0,
			)
		)

	def update_item(source, target, source_parent):
		# qty is for packed items, because packed items don't have stock_qty field
		target.project = source_parent.project
		target.qty = get_remaining_qty(source)
		target.stock_qty = flt(target.qty) * flt(target.conversion_factor)

		args = target.as_dict().copy()
		args.update(
			{
				"company": source_parent.get("company"),
				"price_list": frappe.db.get_single_value("Buying Settings", "buying_price_list"),
				"currency": source_parent.get("currency"),
				"conversion_rate": source_parent.get("conversion_rate"),
			}
		)

		# target.rate = flt(
		# 	get_price_list_rate(args=args, item_doc=frappe.get_cached_doc("Item", target.item_code)).get(
		# 		"price_list_rate"
		# 	)
		# )
		target.amount = target.qty * target.rate

	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {"doctype": "Material Request", "validation": {"docstatus": ["=", 1]}},
			"Packed Item": {
				"doctype": "Material Request Item",
				"field_map": {"parent": "sales_order", "uom": "stock_uom"},
				"postprocess": update_item,
			},
			"Sales Order Item": {
				"doctype": "Material Request Item",
				"field_map": {"name": "sales_order_item", "parent": "sales_order"},
				"condition": lambda item: not frappe.db.exists(
					"Product Bundle", {"name": item.item_code, "disabled": 0}
				)
				and get_remaining_qty(item) > 0,
				"postprocess": update_item,
			},
		},
		target_doc,
	)

	return doc


@frappe.whitelist()
def make_project(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.project_type = "External"
		doc.project_name = source.name

	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Project",
				"validation": {"docstatus": ["=", 1]},
				"field_map": {
					"name": "sales_order",
					"base_grand_total": "estimated_costing",
					"net_total": "total_sales_amount",
				},
			},
		},
		target_doc,
		postprocess,
	)

	return doc


@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None, kwargs=None):
	from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
	from erpnext.stock.doctype.stock_reservation_entry.stock_reservation_entry import (
		get_sre_details_for_voucher,
		get_sre_reserved_qty_details_for_voucher,
		get_ssb_bundle_for_voucher,
	)

	if not kwargs:
		kwargs = {
			"for_reserved_stock": frappe.flags.args and frappe.flags.args.for_reserved_stock,
			"skip_item_mapping": frappe.flags.args and frappe.flags.args.skip_item_mapping,
		}

	kwargs = frappe._dict(kwargs)

	sre_details = {}
	if kwargs.for_reserved_stock:
		sre_details = get_sre_reserved_qty_details_for_voucher("Sales Order", source_name)

	mapper = {
		"Sales Order": {"doctype": "Delivery Note", "validation": {"docstatus": ["=", 1]}},
		"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
		"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
	}

	def set_missing_values(source, target):
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")
		target.run_method("set_use_serial_batch_fields")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Delivery Note", "company_address", target.company_address))

		# if invoked in bulk creation, validations are ignored and thus this method is nerver invoked
		if frappe.flags.bulk_transaction:
			# set target items names to ensure proper linking with packed_items
			target.set_new_name()

		make_packing_list(target)

	def condition(doc):
		if doc.name in sre_details:
			del sre_details[doc.name]
			return False

		# make_mapped_doc sets js `args` into `frappe.flags.args`
		if frappe.flags.args and frappe.flags.args.delivery_dates:
			if cstr(doc.delivery_date) not in frappe.flags.args.delivery_dates:
				return False
		if frappe.flags.args and frappe.flags.args.until_delivery_date:
			if cstr(doc.delivery_date) > frappe.flags.args.until_delivery_date:
				return False

		return abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1

	def update_item(source, target, source_parent):
		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
		target.qty = flt(source.qty) - flt(source.delivered_qty)

		item = get_item_defaults(target.item_code, source_parent.company)
		item_group = get_item_group_defaults(target.item_code, source_parent.company)

		if item:
			target.cost_center = (
				frappe.db.get_value("Project", source_parent.project, "cost_center")
				or item.get("buying_cost_center")
				or item_group.get("buying_cost_center")
			)

	if not kwargs.skip_item_mapping:
		mapper["Sales Order Item"] = {
			"doctype": "Delivery Note Item",
			"field_map": {
				"rate": "rate",
				"name": "so_detail",
				"parent": "against_sales_order",
			},
			"condition": condition,
			"postprocess": update_item,
		}

	so = frappe.get_doc("Sales Order", source_name)
	target_doc = get_mapped_doc("Sales Order", so.name, mapper, target_doc)

	if not kwargs.skip_item_mapping and kwargs.for_reserved_stock:
		sre_list = get_sre_details_for_voucher("Sales Order", source_name)

		if sre_list:

			def update_dn_item(source, target, source_parent):
				update_item(source, target, so)

			so_items = {d.name: d for d in so.items if d.stock_reserved_qty}

			for sre in sre_list:
				if not condition(so_items[sre.voucher_detail_no]):
					continue

				dn_item = get_mapped_doc(
					"Sales Order Item",
					sre.voucher_detail_no,
					{
						"Sales Order Item": {
							"doctype": "Delivery Note Item",
							"field_map": {
								"rate": "rate",
								"name": "so_detail",
								"parent": "against_sales_order",
							},
							"postprocess": update_dn_item,
						}
					},
					ignore_permissions=True,
				)

				dn_item.qty = flt(sre.reserved_qty) * flt(dn_item.get("conversion_factor", 1))

				if sre.reservation_based_on == "Serial and Batch" and (sre.has_serial_no or sre.has_batch_no):
					dn_item.serial_and_batch_bundle = get_ssb_bundle_for_voucher(sre)

				target_doc.append("items", dn_item)
			else:
				# Correct rows index.
				for idx, item in enumerate(target_doc.items):
					item.idx = idx + 1

	if not kwargs.skip_item_mapping and frappe.flags.bulk_transaction and not target_doc.items:
		# the (date) condition filter resulted in an unintendedly created empty DN; remove it
		del target_doc
		return

	# Should be called after mapping items.
	set_missing_values(so, target_doc)

	return target_doc


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False):
	def postprocess(source, target):
		set_missing_values(source, target)
		# Get the advance paid Journal Entries in Sales Invoice Advance
		if target.get("allocate_advances_automatically"):
			target.set_advances()

	def set_missing_values(source, target):
		target.flags.ignore_permissions = True
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")
		target.run_method("set_use_serial_batch_fields")

		if source.company_address:
			target.update({"company_address": source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", "company_address", target.company_address))

		# set the redeem loyalty points if provided via shopping cart
		if source.loyalty_points and source.order_type == "Shopping Cart":
			target.redeem_loyalty_points = 1

		target.debit_to = get_party_account("Customer", source.customer, source.company)

	def update_item(source, target, source_parent):
		target.amount = flt(source.amount) - flt(source.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = (
			target.amount / flt(source.rate)
			if (source.rate and source.billed_amt)
			else source.qty - source.returned_qty
		)

		if source_parent.project:
			target.cost_center = frappe.db.get_value("Project", source_parent.project, "cost_center")
		if target.item_code:
			item = get_item_defaults(target.item_code, source_parent.company)
			item_group = get_item_group_defaults(target.item_code, source_parent.company)
			cost_center = item.get("selling_cost_center") or item_group.get("selling_cost_center")

			if cost_center:
				target.cost_center = cost_center

	doclist = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Sales Invoice",
				"field_map": {
					"party_account_currency": "party_account_currency",
					"payment_terms_template": "payment_terms_template",
				},
				"field_no_map": ["payment_terms_template"],
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Sales Invoice Item",
				"field_map": {
					"name": "so_detail",
					"parent": "sales_order",
				},
				"postprocess": update_item,
				"condition": lambda doc: doc.qty
				and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
			},
			"Sales Taxes and Charges": {"doctype": "Sales Taxes and Charges", "add_if_empty": True},
			"Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
		},
		target_doc,
		postprocess,
		ignore_permissions=ignore_permissions,
	)

	automatically_fetch_payment_terms = cint(
		frappe.db.get_single_value("Accounts Settings", "automatically_fetch_payment_terms")
	)
	if automatically_fetch_payment_terms:
		doclist.set_payment_schedule()

	return doclist


@frappe.whitelist()
def make_maintenance_schedule(source_name, target_doc=None):
	maint_schedule = frappe.db.sql(
		"""select t1.name
		from `tabMaintenance Schedule` t1, `tabMaintenance Schedule Item` t2
		where t2.parent=t1.name and t2.sales_order=%s and t1.docstatus=1""",
		source_name,
	)

	if not maint_schedule:
		doclist = get_mapped_doc(
			"Sales Order",
			source_name,
			{
				"Sales Order": {"doctype": "Maintenance Schedule", "validation": {"docstatus": ["=", 1]}},
				"Sales Order Item": {
					"doctype": "Maintenance Schedule Item",
					"field_map": {"parent": "sales_order"},
				},
			},
			target_doc,
		)

		return doclist


@frappe.whitelist()
def make_maintenance_visit(source_name, target_doc=None):
	visit = frappe.db.sql(
		"""select t1.name
		from `tabMaintenance Visit` t1, `tabMaintenance Visit Purpose` t2
		where t2.parent=t1.name and t2.prevdoc_docname=%s
		and t1.docstatus=1 and t1.completion_status='Fully Completed'""",
		source_name,
	)

	if not visit:
		doclist = get_mapped_doc(
			"Sales Order",
			source_name,
			{
				"Sales Order": {"doctype": "Maintenance Visit", "validation": {"docstatus": ["=", 1]}},
				"Sales Order Item": {
					"doctype": "Maintenance Visit Purpose",
					"field_map": {"parent": "prevdoc_docname", "parenttype": "prevdoc_doctype"},
				},
			},
			target_doc,
		)

		return doclist


@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Gantt / Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	from frappe.desk.calendar import get_event_conditions

	conditions = get_event_conditions("Sales Order", filters)

	data = frappe.db.sql(
		"""
		select
			distinct `tabSales Order`.name, `tabSales Order`.customer_name, `tabSales Order`.status,
			`tabSales Order`.delivery_status, `tabSales Order`.billing_status,
			`tabSales Order Item`.delivery_date
		from
			`tabSales Order`, `tabSales Order Item`
		where `tabSales Order`.name = `tabSales Order Item`.parent
			and `tabSales Order`.skip_delivery_note = 0
			and (ifnull(`tabSales Order Item`.delivery_date, '0000-00-00')!= '0000-00-00') \
			and (`tabSales Order Item`.delivery_date between %(start)s and %(end)s)
			and `tabSales Order`.docstatus < 2
			{conditions}
		""".format(
			conditions=conditions
		),
		{"start": start, "end": end},
		as_dict=True,
		update={"allDay": 0},
	)
	return data


@frappe.whitelist()
def make_purchase_order_for_default_supplier(source_name, selected_items=None, target_doc=None):
	"""Creates Purchase Order for each Supplier. Returns a list of doc objects."""

	from erpnext.setup.utils import get_exchange_rate

	if not selected_items:
		return

	if isinstance(selected_items, str):
		selected_items = json.loads(selected_items)

	def set_missing_values(source, target):
		target.supplier = supplier
		target.currency = frappe.db.get_value(
			"Supplier", filters={"name": supplier}, fieldname=["default_currency"]
		)
		company_currency = frappe.db.get_value(
			"Company", filters={"name": target.company}, fieldname=["default_currency"]
		)

		target.conversion_rate = get_exchange_rate(target.currency, company_currency, args="for_buying")

		target.apply_discount_on = ""
		target.additional_discount_percentage = 0.0
		target.discount_amount = 0.0
		target.inter_company_order_reference = ""
		target.shipping_rule = ""

		default_price_list = frappe.get_value("Supplier", supplier, "default_price_list")
		if default_price_list:
			target.buying_price_list = default_price_list

		if any(item.delivered_by_supplier == 1 for item in source.items):
			if source.shipping_address_name:
				target.shipping_address = source.shipping_address_name
				target.shipping_address_display = source.shipping_address
			else:
				target.shipping_address = source.customer_address
				target.shipping_address_display = source.address_display

			target.customer_contact_person = source.contact_person
			target.customer_contact_display = source.contact_display
			target.customer_contact_mobile = source.contact_mobile
			target.customer_contact_email = source.contact_email

		else:
			target.customer = ""
			target.customer_name = ""

		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
		target.schedule_date = source.delivery_date
		target.qty = flt(source.qty) - (flt(source.ordered_qty) / flt(source.conversion_factor))
		target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
		target.project = source_parent.project

	suppliers = [item.get("supplier") for item in selected_items if item.get("supplier")]
	suppliers = list(dict.fromkeys(suppliers))  # remove duplicates while preserving order

	items_to_map = [item.get("item_code") for item in selected_items if item.get("item_code")]
	items_to_map = list(set(items_to_map))

	if not suppliers:
		frappe.throw(
			_("Please set a Supplier against the Items to be considered in the Purchase Order.")
		)

	purchase_orders = []
	for supplier in suppliers:
		doc = get_mapped_doc(
			"Sales Order",
			source_name,
			{
				"Sales Order": {
					"doctype": "Purchase Order",
					"field_no_map": [
						"address_display",
						"contact_display",
						"contact_mobile",
						"contact_email",
						"contact_person",
						"taxes_and_charges",
						"shipping_address",
						"terms",
					],
					"validation": {"docstatus": ["=", 1]},
				},
				"Sales Order Item": {
					"doctype": "Purchase Order Item",
					"field_map": [
						["name", "sales_order_item"],
						["parent", "sales_order"],
						["stock_uom", "stock_uom"],
						["uom", "uom"],
						["conversion_factor", "conversion_factor"],
						["delivery_date", "schedule_date"],
					],
					"field_no_map": [
						"rate",
						"price_list_rate",
						"item_tax_template",
						"discount_percentage",
						"discount_amount",
						"pricing_rules",
					],
					"postprocess": update_item,
					"condition": lambda doc: doc.ordered_qty < doc.stock_qty
					and doc.supplier == supplier
					and doc.item_code in items_to_map,
				},
			},
			target_doc,
			set_missing_values,
		)

		doc.insert()
		frappe.db.commit()
		purchase_orders.append(doc)

	return purchase_orders


@frappe.whitelist()
def make_purchase_order(source_name, selected_items=None, target_doc=None):
	if not selected_items:
		return

	if isinstance(selected_items, str):
		selected_items = json.loads(selected_items)

	items_to_map = [
		item.get("item_code")
		for item in selected_items
		if item.get("item_code") and item.get("item_code")
	]
	items_to_map = list(set(items_to_map))

	def is_drop_ship_order(target):
		drop_ship = True
		for item in target.items:
			if not item.delivered_by_supplier:
				drop_ship = False
				break

		return drop_ship

	def set_missing_values(source, target):
		target.supplier = ""
		target.apply_discount_on = ""
		target.additional_discount_percentage = 0.0
		target.discount_amount = 0.0
		target.inter_company_order_reference = ""
		target.shipping_rule = ""

		if is_drop_ship_order(target):
			target.customer = source.customer
			target.customer_name = source.customer_name
			target.shipping_address = source.shipping_address_name
		else:
			target.customer = target.customer_name = target.shipping_address = None

		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
		target.schedule_date = source.delivery_date
		target.qty = flt(source.qty) - (flt(source.ordered_qty) / flt(source.conversion_factor))
		target.stock_qty = flt(source.stock_qty) - flt(source.ordered_qty)
		target.project = source_parent.project

	def update_item_for_packed_item(source, target, source_parent):
		target.qty = flt(source.qty) - flt(source.ordered_qty)

	# po = frappe.get_list("Purchase Order", filters={"sales_order":source_name, "supplier":supplier, "docstatus": ("<", "2")})
	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Purchase Order",
				"field_no_map": [
					"address_display",
					"contact_display",
					"contact_mobile",
					"contact_email",
					"contact_person",
					"taxes_and_charges",
					"shipping_address",
					"terms",
				],
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "sales_order_item"],
					["parent", "sales_order"],
					["stock_uom", "stock_uom"],
					["uom", "uom"],
					["conversion_factor", "conversion_factor"],
					["delivery_date", "schedule_date"],
				],
				"field_no_map": [
					"rate",
					"price_list_rate",
					"item_tax_template",
					"discount_percentage",
					"discount_amount",
					"supplier",
					"pricing_rules",
				],
				"postprocess": update_item,
				"condition": lambda doc: doc.ordered_qty < doc.stock_qty
				and doc.item_code in items_to_map
				and not is_product_bundle(doc.item_code),
			},
			"Packed Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "sales_order_packed_item"],
					["parent", "sales_order"],
					["uom", "uom"],
					["conversion_factor", "conversion_factor"],
					["parent_item", "product_bundle"],
					["rate", "rate"],
				],
				"field_no_map": [
					"price_list_rate",
					"item_tax_template",
					"discount_percentage",
					"discount_amount",
					"supplier",
					"pricing_rules",
				],
				"postprocess": update_item_for_packed_item,
				"condition": lambda doc: doc.parent_item in items_to_map,
			},
		},
		target_doc,
		set_missing_values,
	)

	set_delivery_date(doc.items, source_name)

	return doc


def set_delivery_date(items, sales_order):
	delivery_dates = frappe.get_all(
		"Sales Order Item", filters={"parent": sales_order}, fields=["delivery_date", "item_code"]
	)

	delivery_by_item = frappe._dict()
	for date in delivery_dates:
		delivery_by_item[date.item_code] = date.delivery_date

	for item in items:
		if item.product_bundle:
			item.schedule_date = delivery_by_item[item.product_bundle]


def is_product_bundle(item_code):
	return frappe.db.exists("Product Bundle", {"name": item_code, "disabled": 0})


@frappe.whitelist()
def make_work_orders(items, sales_order, company, project=None):
	"""Make Work Orders against the given Sales Order for the given `items`"""
	items = json.loads(items).get("items")
	out = []

	for i in items:
		if not i.get("bom"):
			frappe.throw(_("Please select BOM against item {0}").format(i.get("item_code")))
		if not i.get("pending_qty"):
			frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))

		work_order = frappe.get_doc(
			dict(
				doctype="Work Order",
				production_item=i["item_code"],
				bom_no=i.get("bom"),
				qty=i["pending_qty"],
				company=company,
				sales_order=sales_order,
				sales_order_item=i["sales_order_item"],
				project=project,
				fg_warehouse=i["warehouse"],
				description=i["description"],
			)
		).insert()
		work_order.set_work_order_operations()
		work_order.flags.ignore_mandatory = True
		work_order.save()
		out.append(work_order)

	return [p.name for p in out]


@frappe.whitelist()
def update_status(status, name):
	so = frappe.get_doc("Sales Order", name)
	# so.update_status(status)


@frappe.whitelist()
def make_raw_material_request(items, company, sales_order, project=None):
	if not frappe.has_permission("Sales Order", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if isinstance(items, str):
		items = frappe._dict(json.loads(items))

	for item in items.get("items"):
		item["include_exploded_items"] = items.get("include_exploded_items")
		item["ignore_existing_ordered_qty"] = items.get("ignore_existing_ordered_qty")
		item["include_raw_materials_from_sales_order"] = items.get(
			"include_raw_materials_from_sales_order"
		)

	items.update({"company": company, "sales_order": sales_order})

	raw_materials = get_items_for_material_requests(items)
	if not raw_materials:
		frappe.msgprint(
			_("Material Request not created, as quantity for Raw Materials already available.")
		)
		return

	material_request = frappe.new_doc("Material Request")
	material_request.update(
		dict(
			doctype="Material Request",
			transaction_date=nowdate(),
			company=company,
			material_request_type="Purchase",
		)
	)
	for item in raw_materials:
		item_doc = frappe.get_cached_doc("Item", item.get("item_code"))

		schedule_date = add_days(nowdate(), cint(item_doc.lead_time_days))
		row = material_request.append(
			"items",
			{
				"item_code": item.get("item_code"),
				"qty": item.get("quantity"),
				"schedule_date": schedule_date,
				"warehouse": item.get("warehouse"),
				"sales_order": sales_order,
				"project": project,
			},
		)

		if not (strip_html(item.get("description")) and strip_html(item_doc.description)):
			row.description = item_doc.item_name or item.get("item_code")

	material_request.insert()
	material_request.flags.ignore_permissions = 1
	material_request.run_method("set_missing_values")
	material_request.submit()
	return material_request


@frappe.whitelist()
def make_inter_company_purchase_order(source_name, target_doc=None):
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_inter_company_transaction

	return make_inter_company_transaction("Sales Order", source_name, target_doc)


@frappe.whitelist()
def create_pick_list(source_name, target_doc=None):
	from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle

	def validate_sales_order():
		so = frappe.get_doc("Sales Order", source_name)
		for item in so.items:
			if item.stock_reserved_qty > 0:
				frappe.throw(
					_(
						"Cannot create a pick list for Sales Order {0} because it has reserved stock. Please unreserve the stock in order to create a pick list."
					).format(frappe.bold(source_name))
				)

	def update_item_quantity(source, target, source_parent) -> None:
		picked_qty = flt(source.picked_qty) / (flt(source.conversion_factor) or 1)
		qty_to_be_picked = flt(source.qty) - max(picked_qty, flt(source.delivered_qty))

		target.qty = qty_to_be_picked
		target.stock_qty = qty_to_be_picked * flt(source.conversion_factor)

	def update_packed_item_qty(source, target, source_parent) -> None:
		qty = flt(source.qty)
		for item in source_parent.items:
			if source.parent_detail_docname == item.name:
				picked_qty = flt(item.picked_qty) / (flt(item.conversion_factor) or 1)
				pending_percent = (item.qty - max(picked_qty, item.delivered_qty)) / item.qty
				target.qty = target.stock_qty = qty * pending_percent
				return

	def should_pick_order_item(item) -> bool:
		return (
			abs(item.delivered_qty) < abs(item.qty)
			and item.delivered_by_supplier != 1
			and not is_product_bundle(item.item_code)
		)

	# Don't allow a Pick List to be created against a Sales Order that has reserved stock.
	validate_sales_order()

	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Pick List",
				"field_map": {"set_warehouse": "parent_warehouse"},
				"validation": {"docstatus": ["=", 1]},
			},
			"Sales Order Item": {
				"doctype": "Pick List Item",
				"field_map": {"parent": "sales_order", "name": "sales_order_item"},
				"postprocess": update_item_quantity,
				"condition": should_pick_order_item,
			},
			"Packed Item": {
				"doctype": "Pick List Item",
				"field_map": {
					"parent": "sales_order",
					"name": "sales_order_item",
					"parent_detail_docname": "product_bundle_item",
				},
				"field_no_map": ["picked_qty"],
				"postprocess": update_packed_item_qty,
			},
		},
		target_doc,
	)

	doc.purpose = "Delivery"

	doc.set_item_locations()

	return doc


def update_produced_qty_in_so_item(sales_order, sales_order_item):
	# for multiple work orders against same sales order item
	linked_wo_with_so_item = frappe.db.get_all(
		"Work Order",
		["produced_qty"],
		{"sales_order_item": sales_order_item, "sales_order": sales_order, "docstatus": 1},
	)

	total_produced_qty = 0
	for wo in linked_wo_with_so_item:
		total_produced_qty += flt(wo.get("produced_qty"))

	if not total_produced_qty and frappe.flags.in_patch:
		return

	frappe.db.set_value("Sales Order Item", sales_order_item, "produced_qty", total_produced_qty)


@frappe.whitelist()
def get_work_order_items(sales_order, for_raw_material_request=0):
	"""Returns items with BOM that already do not have a linked work order"""
	if sales_order:
		so = frappe.get_doc("Sales Order", sales_order)

		wo = qb.DocType("Work Order")

		items = []
		item_codes = [i.item_code for i in so.items]
		product_bundle_parents = [
			pb.new_item_code
			for pb in frappe.get_all(
				"Product Bundle", {"new_item_code": ["in", item_codes], "disabled": 0}, ["new_item_code"]
			)
		]

		for table in [so.items, so.packed_items]:
			for i in table:
				bom = get_default_bom(i.item_code)
				stock_qty = i.qty if i.doctype == "Packed Item" else i.stock_qty

				if not for_raw_material_request:
					total_work_order_qty = flt(
						qb.from_(wo)
						.select(Sum(wo.qty))
						.where(
							(wo.production_item == i.item_code)
							& (wo.sales_order == so.name)
							& (wo.sales_order_item == i.name)
							& (wo.docstatus.lt(2))
						)
						.run()[0][0]
					)
					pending_qty = stock_qty - total_work_order_qty
				else:
					pending_qty = stock_qty

				if pending_qty and i.item_code not in product_bundle_parents:
					items.append(
						dict(
							name=i.name,
							item_code=i.item_code,
							description=i.description,
							bom=bom or "",
							warehouse=i.warehouse,
							pending_qty=pending_qty,
							required_qty=pending_qty if for_raw_material_request else 0,
							sales_order_item=i.name,
						)
					)

		return items


# Custom Script

# @frappe.whitelist()
# def make_approved(docname):
#     # Your logic here
#     doc = frappe.get_doc('Sales Order', docname)
    
#     # Iterate through items in the child table
#     # for item in doc.items:
#     #     # Update item status before inserting and submitting Rental Order
#     #     if update_item_status(item.item_code):
#     #         # Create a new Rental Order document
#     #         new_rental_order = frappe.new_doc('Rental Order')
            
#     #         # Set fields based on the original document
#     #         new_rental_order.customer = doc.customer
#     #         new_rental_order.start_date = doc.start_date
#     #         new_rental_order.end_date = doc.end_date
#     #         new_rental_order.sales_order_id = doc.name
#     #         new_rental_order.order_type = doc.order_type
#     #         new_rental_order.taxes_and_charges = doc.taxes_and_charges

#     #         # Add other fields as needed
            
#     #         # Create a new items child table in the Rental Order document
#     #         new_item = new_rental_order.append('items')
            
#     #         # Set fields based on the item in the original document's child table
#     #         new_item.item_group = item.item_group
#     #         new_item.item_code1 = item.item_code
#     #         new_item.qty = item.qty
#     #         new_item.rate = item.rate
#     #         new_item.amount = item.amount
#     #         new_item.rental_tax_rate = item.rental_tax_rate
#     #         new_item.tax_amount = item.tax_amount
#     #         new_item.line_total = item.line_total
#     #         new_item.item_tax_template = item.item_tax_template
#     #         # Add other fields as needed

#     #         # Set new_rental_order.total based on the sum of item.amount and taxes
#     #         new_rental_order.total = item.amount

#     #         total_taxes_and_charges = 0  # Initialize the variable to store the sum of tax_amount
            
#     #         # Iterate through taxes in the original document
#     #         for tax in doc.get('taxes', []):
#     #             new_tax = new_rental_order.append('taxes')
#     #             new_tax.charge_type = tax.charge_type
#     #             new_tax.account_head = tax.account_head
#     #             new_tax.description = tax.description
#     #             new_tax.cost_center = tax.cost_center
#     #             new_tax.rate = tax.rate
#     #             new_tax.tax_amount = item.amount * tax.rate / 100
#     #             total_taxes_and_charges += new_tax.tax_amount  # Add tax_amount to the total

#     #         # Set new_rental_order.total_taxes_and_charges based on the sum of tax_amount
#     #         new_rental_order.total_taxes_and_charges = total_taxes_and_charges

#     #         # Set new_rental_order.grand_total and new_rental_order.rounded_total
#     #         new_rental_order.grand_total = new_rental_order.total + new_rental_order.total_taxes_and_charges
#     #         new_rental_order.rounded_total = new_rental_order.grand_total

#     #         # Save the new Rental Order document
#     #         new_rental_order.insert()
#     #         new_rental_order.submit()
    
#     # Update the status of the original document
#     doc.status = 'Approved'
#     doc.save()

#     return "Approved Success"


@frappe.whitelist()
def make_approved(docname):
    try:
        # Fetch Sales Order Item records with the given docname as parent
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name", "item_code"])

        # Iterate through the fetched Sales Order Items
        for item in sales_order_items:
            # Fetch the Item document
            item_doc = frappe.get_doc('Item', item.item_code)

            # Update the item status to "Reserved" if it's available
            if item_doc.status == 'Available':
                item_doc.status = 'Reserved'
                item_doc.save()
                frappe.msgprint(f'Item {item.item_code} status updated to Reserved')
            else:
                frappe.msgprint(f'Item {item.item_code} is already Booked')
                # If an item is already booked, don't continue to the next steps
                break

            # Update child_status to "Approved" for items whose status was successfully updated
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "Approved"
            sales_order_item.save()

        # Check if all items in the Sales Order have their status as "Reserved" in the Item master
        # if all(frappe.get_value("Item", {"item_code": item.item_code}, "status") == "Reserved" for item in sales_order_items):
            # Execute your additional code here
            sales_order = frappe.get_doc("Sales Order", docname)
            sales_order.status = "Approved"
            sales_order.save()

        return "Approved Success"

    except Exception as e:
        # Log the error details without the title parameter
        frappe.log_error(f"Error in make_approved: {e}")
        # Reraise the exception to propagate it
        raise


@frappe.whitelist()
def make_rental_device_assign(docname, item_group, item_code):
    try:
        # Your logic here
        doc = frappe.get_doc('Sales Order', docname)

        # Check if the user has permission to update the Item doctype
        frappe.only_for('Item', 'write')

        item_status = frappe.get_value("Item", item_code, "status")

        if item_status == "Available":
            item_doc = frappe.get_doc("Item", item_code)
            item_doc.status = "Reserved"
            item_doc.save()
            # Optionally, you may want to commit the changes to the database
            frappe.db.commit()

            # Set values for rental device and update status
            doc.item_group = item_group
            doc.item_code = item_code
            doc.status = 'Rental Device Assigned'
            doc.save()

            return "Rental Device Assigned Success"
        else:
            frappe.msgprint("Item is not available for reservation.")

    except Exception as e:
        frappe.log_error(f"Error in make_rental_device_assign: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")


# @frappe.whitelist()
# def get_item_groups():
#     item_groups = frappe.get_all('Sales Order Item', filters={'docstatus': 1}, distinct=True, pluck='item_group')
#     return item_groups




# @frappe.whitelist()
# def make_ready_for_delivery(docname):
#     # Your logic here
#     # Get the 'Sales Order' document
#     rental_group_order = frappe.get_doc('Sales Order', docname)
    
#     # Update the status of the 'Sales Order'
#     rental_group_order.status = 'Ready for Delivery'
#     rental_group_order.save()

# 	sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

#     # Iterate through the fetched Sales Order Items and update their child_status to "Approved"
#     for item in sales_order_items:
#         sales_order_item = frappe.get_doc("Sales Order Item", item.name)
#         sales_order_item.child_status = "Ready for Delivery"
#         sales_order_item.save()

#     # Iterate through related 'Rental Order' documents and update their status
#     # for rental_order in frappe.get_all('Rental Order', filters={'sales_order_id': docname}):
#     #     rental_order_doc = frappe.get_doc('Rental Order', rental_order.name)
#     #     rental_order_doc.status = 'Ready for Delivery'
#     #     rental_order_doc.save()

#     return "Ready for Delivery Success"


@frappe.whitelist()
def make_ready_for_delivery(docname,technician_name,technician_mobile):
    # Get the 'Sales Order' document
    rental_group_order = frappe.get_doc('Sales Order', docname)
    
    # Update the status of the 'Sales Order'
    rental_group_order.status = 'Ready for Delivery'
    rental_group_order.technician_name_before_delivered = technician_name
    rental_group_order.technician_mobile_before_delivered = technician_mobile
    rental_group_order.save()

    # Fetch Sales Order Item records with the given docname as parent
    sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

    # Iterate through the fetched Sales Order Items and update their child_status to "Ready for Delivery"
    for item in sales_order_items:
        sales_order_item = frappe.get_doc("Sales Order Item", item.name)
        sales_order_item.child_status = "Ready for Delivery"
        sales_order_item.technician_name_before_delivered = technician_name
        sales_order_item.technician_mobile_before_delivered = technician_mobile
        sales_order_item.save()

    return "Ready for Delivery Success"




def apply_item_filter(doc, method):
    for item in doc.items:
        # Check if the item group is 'Rental'
        if frappe.get_value('Item', item.item_code, 'item_group') != 'Rental':
            frappe.throw(f"Item {item.item_code} is not in the 'Rental' item group. Remove it from the Sales Order.")

@frappe.whitelist()
def make_dispatch(docname, dispatch_date):
    try:
        # Get the 'Sales Order' document
        rental_sales_order = frappe.get_doc('Sales Order', docname)

        # Update Sales Order with the entered dispatch_date
        rental_sales_order.dispatch_date = dispatch_date
        rental_sales_order.status = "DISPATCHED"
        rental_sales_order.save()

        # Fetch Sales Order Item records with the given docname as parent
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

        # Iterate through the fetched Sales Order Items and update their child_status to "DISPATCHED"
        for item in sales_order_items:
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "DISPATCHED"
            sales_order_item.dispatch_date = dispatch_date
            sales_order_item.save()

        # Optionally, you may want to commit the changes to the database
        # frappe.db.commit()

        return "Rental Device DISPATCHED Success"

    except Exception as e:
        # Log any errors that occur
        frappe.log_error(f"Error in make_dispatch: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")


@frappe.whitelist()
def make_rental_device_assign(docname, item_group, item_code):
    try:
        doc = frappe.get_doc('Sales Order', docname)

        # Check if the user has permission to update or cancel the Item doctype
        frappe.only_for('Item', ['write', 'cancel'])

        item_status = frappe.get_value("Item", item_code, "status")

        if item_status == "Available":
            # Update Item status to Reserved
            item_doc = frappe.get_doc("Item", item_code)
            item_doc.status = "Reserved"
            item_doc.save()
            frappe.db.commit()

            # Set values for rental device and update status
            doc.item_group = item_group
            doc.item_code = item_code
            doc.status = 'Rental Device Assigned'
            doc.save()

            return "Rental Device Assigned Success"
        else:
            frappe.msgprint("Item is not available for reservation.")

    except frappe.DoesNotExistError:
        # Handle the case where the sale order is canceled
        # Update Item status to Available
        item_doc = frappe.get_doc("Item", item_code)
        item_doc.status = "Available"
        item_doc.save()
        frappe.db.commit()

        # Set values for rental device and update status
        doc.item_group = None
        doc.item_code = None
        doc.status = 'Cancelled'
        doc.save()

        return "Rental Device Assignment Cancelled"

    except Exception as e:
        frappe.log_error(f"Error in make_rental_device_assign: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")


import frappe

@frappe.whitelist()
def make_delivered(docname, delivered_date):
    try:
        # Get the 'Sales Order' document
        rental_group_order = frappe.get_doc('Sales Order', docname)

        # Update each child item and its status
        for item in rental_group_order.items:
            # Get the item code from the child table
            item_code = item.item_code
            # Update the item status to "Rented Out"
            item_doc = frappe.get_doc("Item", item_code)
            item_doc.status = "Rented Out"
            item_doc.save()

        # Update values for rental device and update status in Sales Order
        rental_group_order.rental_delivery_date = delivered_date
        rental_group_order.status = 'Active'
        rental_group_order.save()

        # Update status in related Sales Order Items
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])
        for item in sales_order_items:
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "Active"
            sales_order_item.rental_delivery_date = delivered_date
            sales_order_item.save()

        return "Rental Device DELIVERED Success"

    except Exception as e:
        # Log any errors that occur
        frappe.log_error(f"Error in make_delivered: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")

@frappe.whitelist()
def make_ready_for_pickup(docname, pickup_date, pickup_reason,pickup_remark,technician_name,technician_mobile ):
    try:
        # Get the 'Sales Order' document
        doc = frappe.get_doc('Sales Order', docname)

        # Set values for pickup date and update status
        doc.pickup_date = pickup_date
        doc.status = 'Ready for Pickup'
        doc.pickup_reason = pickup_reason
        doc.pickup_remark = pickup_remark
        doc.technician_name_after_delivered = technician_name
        doc.technician_mobile_after_delivered = technician_mobile
        doc.save()

        # Update status and pickup date in related Sales Order Items
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])
        for item in sales_order_items:
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "Ready for Pickup"
            sales_order_item.pickup_date = pickup_date
            sales_order_item.pickup_reason = pickup_reason
            sales_order_item.pickup_remark = pickup_remark
            sales_order_item.technician_name_after_delivered = technician_name
            sales_order_item.technician_mobile_after_delivered = technician_mobile
            sales_order_item.save()

        return "Sales Order is Ready for Pickup"

    except Exception as e:
        # Log any errors that occur
        frappe.log_error(f"Error in make_ready_for_pickup: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")

@frappe.whitelist()
def make_pickedup(docname, pickup_date):
    try:
        # Get the 'Sales Order' document
        doc = frappe.get_doc('Sales Order', docname)

        # Set values for technician name and mobile
        doc.picked_up = pickup_date
        # doc.technician_mobile = technician_mobile

        # Update status to 'Picked Up'
        doc.status = 'Picked Up'
        doc.save()

        # Update status in related Sales Order Items
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])
        for item in sales_order_items:
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "Picked Up"
            sales_order_item.pickup_date = pickup_date
            # sales_order_item.technician_mobile = technician_mobile
            sales_order_item.save()

        return "Sales Order is marked as Picked Up."

    except Exception as e:
        # Log any errors that occur
        frappe.log_error(f"Error in make_pickedup: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")

import ast

@frappe.whitelist()
def make_submitted_to_office(docname, item_code, submitted_date):
    try:
        # Convert the string representation of the list to an actual list
        item_codes = ast.literal_eval(item_code)

        # Get the 'Sales Order' document
        doc = frappe.get_doc('Sales Order', docname)

        # Update status of items to "Available"
        for item_code in item_codes:
            item_doc = frappe.get_doc("Item", item_code)
            item_doc.status = "Available"
            item_doc.save()

        # Set values for submission to office and update status
        doc.submitted_date = submitted_date
        doc.status = 'Submitted to Office'
        doc.save()

        # Update status in related Sales Order Items
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])
        for item in sales_order_items:
            sales_order_item = frappe.get_doc("Sales Order Item", item.name)
            sales_order_item.child_status = "Submitted to Office"
            sales_order_item.submitted_date = submitted_date
            sales_order_item.save()

        return "Submitted to Office Success"

    except Exception as e:
        # Log any errors that occur
        frappe.log_error(f"Error in make_submitted_to_office: {e}")
        frappe.throw("An error occurred while processing the request. Please try again.")

@frappe.whitelist()
def on_hold(docname):
    doc = frappe.get_doc('Sales Order', docname)
    
    # Perform any server-side logic here, e.g., update some fields, perform calculations, etc.
    
    # Update the status to 'On Hold'
    doc.set('status', 'On Hold')
    doc.save()

    frappe.msgprint(_('Document Hold successfully.'))

    return True


# your_module/doctype/rental_group_order/rental_group_order.py
from frappe import _

@frappe.whitelist()
def update_status(docname, new_status):
    doc = frappe.get_doc('Sales Order', docname)
    
    # Perform any server-side logic here, e.g., update some fields, perform calculations, etc.
    
    # Update the status to the new status
    doc.set('status', new_status)
    doc.save()

    # frappe.msgprint(_('Document status updated successfully.'))
    return True



@frappe.whitelist()
def close_rental_order(docname):
    doc = frappe.get_doc('Sales Order', docname)

    # Perform any necessary validation or logic before closing the order

    # Update the status to 'Closed'
    doc.set('status', 'Closed')
    doc.save()

    frappe.msgprint(_('Rental Order Closed successfully.'))
    return True


# custom_script_path/nhk/nhk/doctype/rental_group_order/rental_group_order.py

# import frappe

# @frappe.whitelist()
# def update_item_status_code(itemCode1, docname):
#     item = frappe.get_doc("Item", {"item_code": itemCode1})
#     if item:
#         item.status = "Available"
#         item.save(ignore_permissions=True)
#         update_rental_order_status(itemCode1)

#         # Check if all related Rental Orders are closed
#         rental_orders = frappe.get_all("Rental Order", filters={"rental_group_id": docname}, fields=["status"])
#         all_orders_closed = all(order.get("status") == "Closed" for order in rental_orders)

#         doc = frappe.get_doc("Sales Order", docname)
#         doc.status = "Closed" if all_orders_closed else "Partially Closed"
#         doc.save(ignore_permissions=True)

#         return True
#     else:
#         return False



# import frappe

# @frappe.whitelist()
# def update_rental_order_status(itemCode1):
#     # Retrieve Rental Orders based on the item_code field in the items child table
#     rental_orders = frappe.get_all("Rental Order", filters={"item_code": itemCode1}, fields=["name"])

#     if rental_orders:
#         for rental_order in rental_orders:
#             # Retrieve each rental order document
#             rental_order_doc = frappe.get_doc("Rental Order", rental_order.name)

#             # Set status to "Closed" for each rental order
#             rental_order_doc.status = "Closed"
#             rental_order_doc.save(ignore_permissions=True)

#         return True
#     else:
#         return False

import frappe

@frappe.whitelist()
def sales_order_for_html(sales_order_id):
    sales_order_items = frappe.get_all("Sales Order Item",
                                       filters={"parent": sales_order_id},
                                       fields=["name", "child_status", "item_code", "item_group", "rate", "amount", "tax_amount", "line_total","replaced_item_code"])

    items_data = []
    for item in sales_order_items:
        item_doc = frappe.get_doc("Item", item.item_code)
        item_status = item_doc.status if item_doc else None
        item_data = {
            "name": item.name,
            "child_status": item.child_status,
            "item_code": item.item_code,
            "item_group": item.item_group,
            "rate": item.rate,
            "amount": item.amount,
            "tax_amount": item.tax_amount,
            "line_total": item.line_total,
            "item_status": item_status
        }
        items_data.append(item_data)

    return items_data



@frappe.whitelist()
def update_status_to_ready_for_pickup(item_code, pickup_datetime, docname, child_name,pickupReason,pickupRemark,technician_name,technician_mobile):
    # Retrieve Rental Orders based on the item_code field in the items child table
    sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

    if sales_order_items:
        # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
        if len(sales_order_items) == 1:
            sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
            sales_order_item_doc.child_status = "Ready for Pickup"
            sales_order_item_doc.pickup_date = pickup_datetime
            sales_order_item_doc.pickup_remark = pickupRemark
            sales_order_item_doc.pickup_reason = pickupReason
            sales_order_item_doc.technician_name_after_delivered = technician_name
            sales_order_item_doc.technician_mobile_after_delivered = technician_mobile
            sales_order_item_doc.save(ignore_permissions=True)

            # Retrieve the Sales Order document and update its status
            sales_order_doc = frappe.get_doc("Sales Order", docname)
            sales_order_doc.status = "Ready for Pickup"
            sales_order_doc.pickup_date = pickup_datetime
            sales_order_doc.pickup_remark = pickupRemark
            sales_order_doc.pickup_reason = pickupReason
            sales_order_doc.technician_name_after_delivered = technician_name
            sales_order_doc.technician_mobile_after_delivered = technician_mobile
            sales_order_doc.save(ignore_permissions=True)

            return True
        else:
            # If there are multiple Sales Order Items, update only the Sales Order Item statuses
            sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
            sales_order_item_doc.child_status = "Ready for Pickup"
            sales_order_item_doc.pickup_date = pickup_datetime
            sales_order_item_doc.pickup_remark = pickupRemark
            sales_order_item_doc.pickup_reason = pickupReason
            sales_order_item_doc.technician_name_after_delivered = technician_name
            sales_order_item_doc.technician_mobile_after_delivered = technician_mobile
            sales_order_item_doc.save(ignore_permissions=True)

            return True
    else:
        return False


@frappe.whitelist()
def update_status_to_picked_up(item_code, docname, child_name,picked_up_datetime):
    # Retrieve Rental Orders based on the item_code field in the items child table
    sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

    if sales_order_items:
        # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
        if len(sales_order_items) == 1:
            sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
            sales_order_item_doc.child_status = "Picked Up"
            sales_order_item_doc.pickup_date = picked_up_datetime
            # sales_order_item_doc.technician_mobile = technician_mobile
            # sales_order_item_doc.pickup_date = pickup_datetime
            sales_order_item_doc.save(ignore_permissions=True)

            # Retrieve the Sales Order document and update its status
            sales_order_doc = frappe.get_doc("Sales Order", sales_order_item_doc.parent)
            sales_order_doc.status = "Picked Up"
            sales_order_doc.pickup_date = picked_up_datetime
            # sales_order_doc.technician_mobile = technician_mobile
            # sales_order_doc.pickup_date = pickup_datetime
            sales_order_doc.save(ignore_permissions=True)

            return True
        else:
            # If there are multiple Sales Order Items, update only the Sales Order Item statuses
            sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
            sales_order_item_doc.child_status = "Picked Up"
            sales_order_item_doc.pickup_date = picked_up_datetime
            # sales_order_item_doc.technician_mobile = technician_mobile
            sales_order_item_doc.save(ignore_permissions=True)

            return True
    else:
        return False


# import frappe

# @frappe.whitelist()
# def update_status_to_submitted_to_office(item_code, submission_datetime, docname):
#     try:
#         # Retrieve the item document
#         item = frappe.get_doc("Item", {"item_code": item_code})
#         if item:
#             item.status = "Available"
#             item.save(ignore_permissions=True)
#             update_rental_order_status(item_code)

#             # Check if all related Rental Orders are closed
#             rental_orders = frappe.get_all("Rental Order", filters={"item_code": item_code, "rental_group_id": docname}, fields=["status"])
#             all_orders_closed = all(order.get("status") == "Closed" for order in rental_orders)
#             # print(all_orders_closed)
#             # Update the status of the Sales Order only if all orders are closed
#             if all_orders_closed:
#                 doc = frappe.get_doc("Sales Order", docname)
#                 doc.status = "Closed"
#                 doc.save(ignore_permissions=True)
#             else:
#                 doc = frappe.get_doc("Sales Order", docname)
#                 doc.status = "Partially Closed"
#                 doc.save(ignore_permissions=True)
                
#             return True
#         else:
#             return False
#     except Exception as e:
#         frappe.log_error(f"Error updating status to Submitted to Office: {e}", "Sales Order")
#         return False


import frappe

@frappe.whitelist()
def update_status_to_submitted_to_office(item_code, submission_datetime, docname, child_name):
    try:
        # Retrieve the item document
        item = frappe.get_doc("Item", item_code)
        if item:
            item.status = "Available"
            item.save(ignore_permissions=True)

        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

        if sales_order_items:
            # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
            if len(sales_order_items) == 1:
                sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
                sales_order_item_doc.child_status = "Submitted to Office"
                sales_order_item_doc.submitted_date = submission_datetime
                sales_order_item_doc.save(ignore_permissions=True)

                # Retrieve the Sales Order document and update its status
                sales_order_doc = frappe.get_doc("Sales Order", docname)
                sales_order_doc.status = "Submitted to Office"
                sales_order_doc.submitted_date = submission_datetime
                sales_order_doc.save(ignore_permissions=True)

                return True
            else:
                # If there are multiple Sales Order Items, update only the Sales Order Item statuses
                sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
                sales_order_item_doc.child_status = "Submitted to Office"
                sales_order_item_doc.submitted_date = submission_datetime
                sales_order_item_doc.save(ignore_permissions=True)

                # Check the statuses of all Sales Order Items
                sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["child_status"])

                if sales_order_items:
                    # Check if all Sales Order Items have the status "Submitted to Office"
                    all_submitted_to_office = all(item.get("child_status") == "Submitted to Office" for item in sales_order_items)

                    # Retrieve the Sales Order document
                    sales_order_doc = frappe.get_doc("Sales Order", docname)

                    if all_submitted_to_office:
                        # If all Sales Order Items have the status "Submitted to Office", update Sales Order status
                        sales_order_doc.status = "Submitted to Office"
                    else:
                        # If any Sales Order Item doesn't have the status "Submitted to Office", set status to "Partially Closed"
                        sales_order_doc.status = "Partially Closed"

                    sales_order_doc.save(ignore_permissions=True)
                    return True
                else:
                    # Handle case when there are no sales order items found
                    return False
        else:
            # Handle case when there are no sales order items found
            return False

    except Exception as e:
        frappe.log_error(f"Error updating status to Submitted to Office: {e}", "Sales Order")
        return False




@frappe.whitelist()
def update_status_to_active(item_code, docname, child_name):
    sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

    if sales_order_items:
        # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
        if len(sales_order_items) == 1:
            sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
            sales_order_item_doc.child_status = "Active"
            sales_order_item_doc.pickup_date = ""
            sales_order_item_doc.save(ignore_permissions=True)

            # Retrieve the Sales Order document and update its status
            sales_order_doc = frappe.get_doc("Sales Order", sales_order_item_doc.parent)
            sales_order_doc.status = "Active"
            sales_order_doc.pickup_date = ""
            sales_order_doc.save(ignore_permissions=True)

            return True
        else:
            # If there are multiple Sales Order Items, update only the Sales Order Item statuses
            sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
            sales_order_item_doc.child_status = "Active"
            sales_order_item_doc.pickup_date = ""
            sales_order_item_doc.save(ignore_permissions=True)

            return True
    else:
        return False




@frappe.whitelist()
def update_status_back_to_ready_for_pickup(item_code, docname, child_name):
    sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

    if sales_order_items:
        # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
        if len(sales_order_items) == 1:
            sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
            sales_order_item_doc.child_status = "Ready for Pickup"
            sales_order_item_doc.pickup_date = ""
            sales_order_item_doc.save(ignore_permissions=True)

            # Retrieve the Sales Order document and update its status
            sales_order_doc = frappe.get_doc("Sales Order", sales_order_item_doc.parent)
            sales_order_doc.status = "Ready for Pickup"
            sales_order_doc.pickup_date = ""
            sales_order_doc.save(ignore_permissions=True)

            return True
        else:
            # If there are multiple Sales Order Items, update only the Sales Order Item statuses
            sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
            sales_order_item_doc.child_status = "Ready for Pickup"
            sales_order_item_doc.pickup_date = ""
            sales_order_item_doc.save(ignore_permissions=True)

            return True
    else:
        return False




@frappe.whitelist()
def update_status_to_pickup(item_code, docname, child_name):
    try:
        # Retrieve the item document
        item = frappe.get_doc("Item", item_code)
        if item:
            item.status = "Rented Out"
            item.save(ignore_permissions=True)

        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name"])

        if sales_order_items:
            # If there is only one Sales Order Item, update both Sales Order and Sales Order Item statuses
            if len(sales_order_items) == 1:
                sales_order_item_doc = frappe.get_doc("Sales Order Item", sales_order_items[0].name)
                sales_order_item_doc.child_status = "Picked Up"
                sales_order_item_doc.submitted_date = ""
                sales_order_item_doc.save(ignore_permissions=True)

                # Retrieve the Sales Order document and update its status
                sales_order_doc = frappe.get_doc("Sales Order", docname)
                sales_order_doc.status = "Picked Up"
                sales_order_doc.submitted_date = ""
                sales_order_doc.save(ignore_permissions=True)

                return True
            else:
                # If there are multiple Sales Order Items, update only the Sales Order Item statuses
                sales_order_item_doc = frappe.get_doc("Sales Order Item", {"name": child_name})
                sales_order_item_doc.child_status = "Picked Up"
                sales_order_item_doc.submitted_date = ""
                sales_order_item_doc.save(ignore_permissions=True)

                # Update sales order status to "Active"
                sales_order_items_status = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name", "child_status"])

                all_not_submitted = all(item.child_status != "Submitted to Office" for item in sales_order_items_status)

                # Update sales order status
                sales_order_replace = frappe.get_doc("Sales Order", docname)
                if all_not_submitted:
                    sales_order_replace.status = "Active"
                else:
                    sales_order_replace.status = "Partially Closed"
                sales_order_replace.save()

                return True
                
        else:
            # Handle case when there are no sales order items found
            return False

    except Exception as e:
        frappe.log_error(f"Error updating status to Submitted to Office: {e}", "Sales Order")
        return False




from frappe import _, publish_realtime
from frappe.utils import today, getdate

# Method to change status of overdue Sales Orders
@frappe.whitelist()
def mark_overdue_sales_orders():
    # Get today's date as a datetime.date object
    today_date = getdate(today())
    
    # Get all Sales Orders
    sales_orders = frappe.get_list("Sales Order",
                                   fields=["name", "end_date", "overdue_status", "status"])

    for so in sales_orders:
        end_date = getdate(so.end_date)  # Convert end_date string to datetime.date object
        
        # Check if the status is 'RENEWED'
        if so.status == 'RENEWED':
            # Update overdue_status to 'Renewed'
            frappe.db.set_value("Sales Order", so.name, "overdue_status", "Renewed")
        elif end_date < today_date:
            # Update overdue_status to 'Overdue'
            frappe.db.set_value("Sales Order", so.name, "overdue_status", "Overdue")
        else:
            # Update overdue_status to 'Active'
            frappe.db.set_value("Sales Order", so.name, "overdue_status", "Active")

    # Publish a message to refresh the list view
    # publish_realtime('list_update', "Sales Order")


import frappe

@frappe.whitelist()
def create_renewal_order(sales_order_name):
    # Get original sales order
    original_sales_order = frappe.get_doc("Sales Order", sales_order_name)

    # Create a new sales order based on the original one
    new_sales_order = frappe.copy_doc(original_sales_order)
    new_sales_order.previous_order_id = original_sales_order.name  # Pass original order ID to renewal_order_id
    new_sales_order.insert()

    # Update original sales order status only after the new sales order has been submitted
    # frappe.enqueue(update_original_sales_order_status, original_sales_order=original_sales_order)

    return new_sales_order.name

# def update_original_sales_order_status(original_sales_order):
#     original_sales_order.status = "RENEWED"
#     original_sales_order.save()




@frappe.whitelist()
def get_sales_orders_by_rental_group_id(docname):
    # Fetch sales orders based on the rental group ID
    sales_orders = frappe.get_all("Sales Order",
        filters={"master_order_id": docname},
        fields=["name", "start_date", "end_date", "total_no_of_dates", "rounded_total","status"])
    
    return sales_orders




@frappe.whitelist()
def validate_and_update_payment_status(docname):
    sales_order = frappe.get_doc("Sales Order", docname)
    
    # Access the rounded_total and advance_paid fields from the document object
    rounded_total = sales_order.rounded_total
    advance_paid = sales_order.advance_paid

    # Calculate the balance amount
    balance_amount = rounded_total - advance_paid

    # Update the balance_amount field in the Sales Order document
    sales_order.balance_amount = balance_amount

    # Check if the rounded_total is equal to advance_paid
    if rounded_total == advance_paid:
        # If rounded_total equals advance_paid, set payment_status to 'Paid'
        sales_order.payment_status = 'Paid'
    elif advance_paid == 0:
        # If advance_paid is zero, set payment_status to 'Unpaid'
        sales_order.payment_status = 'UnPaid'
    else:
        # If rounded_total is not equal to advance_paid and advance_paid is not zero,
        # set payment_status to 'Partially Paid'
        sales_order.payment_status = 'Partially Paid'

    sales_order.save()
    
    return balance_amount



@frappe.whitelist()
def validate_and_update_payment_and_security_deposit_status(docname):
    try:
        sales_order = frappe.get_doc("Sales Order", docname)

        # Access the rounded_total and advance_paid fields from the document object
        rounded_total = sales_order.rounded_total
        advance_paid = sales_order.advance_paid

        # Calculate the balance amount
        balance_amount = rounded_total - advance_paid

        # Update the balance_amount field in the Sales Order document
        sales_order.balance_amount = balance_amount

        # Check if the rounded_total is equal to advance_paid
        if rounded_total == advance_paid:
            # If rounded_total equals advance_paid, set payment_status to 'Paid'
            sales_order.payment_status = 'Paid'
        elif advance_paid == 0:
            # If advance_paid is zero, set payment_status to 'Unpaid'
            sales_order.payment_status = 'UnPaid'
        else:
            # If rounded_total is not equal to advance_paid and advance_paid is not zero,
            # set payment_status to 'Partially Paid'
            sales_order.payment_status = 'Partially Paid'

        # Query Journal Entry records based on sales_order_id and security_deposit_type
        journal_entries = frappe.get_all("Journal Entry", 
                                          filters={"sales_order_id": docname, 
                                                   "security_deposite_type": "Cash Received From Client"},
                                          fields=["name", "total_debit"])
        
        # Calculate total debit amount from the filtered journal entries
        total_debit_amount = sum(journal_entry.total_debit for journal_entry in journal_entries)
        
        # Convert sales_order.security_deposit to float
        security_deposit = float(sales_order.security_deposit)

        # Update the paid_security_deposit_amount field
        sales_order.paid_security_deposite_amount = total_debit_amount

        outstanding_security_deposit_amount = security_deposit - total_debit_amount

        # Update the outstanding_security_deposit_amount field
        sales_order.outstanding_security_deposit_amount = outstanding_security_deposit_amount

        # Determine the security deposit status based on the outstanding amount
        if outstanding_security_deposit_amount == 0:
            # If outstanding amount is zero, set security_deposit_status to 'Paid'
            sales_order.security_deposit_status = 'Paid'
        elif outstanding_security_deposit_amount == security_deposit:
            # If outstanding amount is equal to total security deposit, set security_deposit_status to 'Unpaid'
            sales_order.security_deposit_status = 'Unpaid'
        else:
            # If outstanding amount is not zero and not equal to total security deposit, set security_deposit_status to 'Partially Paid'
            sales_order.security_deposit_status = 'Partially Paid'
        
        # Save the changes to the document
        sales_order.save()
        
        # Return True to indicate successful update
        return True

    except Exception as e:
        # Log and raise any exceptions for debugging
        frappe.log_error(frappe.get_traceback(), _("Failed to update payment status"))
        frappe.throw(_("Failed to update payment status. Error: {0}".format(str(e))))



@frappe.whitelist()
def security_deposit_status(docname):
    try:
        sales_order = frappe.get_doc("Sales Order", docname)
        # Query Journal Entry records based on sales_order_id and security_deposit_type
        journal_entries = frappe.get_all("Journal Entry", 
                                          filters={"sales_order_id": docname, 
                                                   "security_deposite_type": "Cash Received From Client"},
                                          fields=["name", "total_debit"])
        
        # Calculate total debit amount from the filtered journal entries
        total_debit_amount = sum(journal_entry.total_debit for journal_entry in journal_entries)
        
        # Print total debit amount for debugging
        # print("Total Debit Amount:", total_debit_amount)
        
        # Convert sales_order.security_deposit to float
        security_deposit = float(sales_order.security_deposit)

        # Update the paid_security_deposit_amount field
        sales_order.paid_security_deposite_amount = total_debit_amount

        outstanding_security_deposit_amount = security_deposit - total_debit_amount

        # Update the outstanding_security_deposit_amount field
        sales_order.outstanding_security_deposit_amount = outstanding_security_deposit_amount

        # Determine the security deposit status based on the outstanding amount
        if outstanding_security_deposit_amount == 0:
            # If outstanding amount is zero, set security_deposit_status to 'Paid'
            sales_order.security_deposit_status = 'Paid'
        elif outstanding_security_deposit_amount == security_deposit:
            # If outstanding amount is equal to total security deposit, set security_deposit_status to 'Unpaid'
            sales_order.security_deposit_status = 'Unpaid'
        else:
            # If outstanding amount is not zero and not equal to total security deposit, set security_deposit_status to 'Partially Paid'
            sales_order.security_deposit_status = 'Partially Paid'
        
        # Save the changes to the document
        sales_order.save()
        
        # Return True to indicate successful update
        return True

    except Exception as e:
        # Log and raise any exceptions for debugging
        frappe.log_error(frappe.get_traceback(), _("Failed to update payment status"))
        frappe.throw(_("Failed to update payment status. Error: {0}".format(str(e))))



# import frappe

# @frappe.whitelist()
# def validateOverlap(docname):
#     previous_order = frappe.get_doc("Sales Order", docname)
#     return {
#         "start_date": previous_order.start_date,
#         "end_date": previous_order.end_date
#     }


def check_overlap(self):
    previous_order = frappe.get_doc("Sales Order", self.previous_order_id)
    if previous_order:
        if self.start_date and self.end_date:
            # Convert string dates to datetime.date objects
            start_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            
            # Check for overlap
            overlap = (start_date <= previous_order.end_date and end_date >= previous_order.start_date)
            return overlap
    return False



@frappe.whitelist()
def item_replacement(item_code, new_item, replacement_date, master_order_id, docname, old_item_status, reason=None):
    try:
        # Add a record in the Rental Order Replaced Item
        rental_order = frappe.new_doc("Rental Order Replaced Item")
        rental_order.master_order_id = master_order_id
        rental_order.sales_order_id = docname
        rental_order.replaced_datetime = replacement_date
        rental_order.old_item = item_code
        rental_order.new_item = new_item
        rental_order.reason = reason
        rental_order.save()
        
        # Update child_status and replacement_date in Sales Order Items
        sales_order_items = frappe.get_all("Sales Order Item", filters={"parent": docname, "item_code": item_code}, fields=["name", "child_status"])
        for item in sales_order_items:
            if item.child_status == "Picked Up":
                sales_order_item = frappe.get_doc("Sales Order Item", item.name)
                sales_order_item.child_status = "Active"
                sales_order_item.replaced_datetime = replacement_date
                sales_order_item.old_item_code = item_code
                sales_order_item.item_code = new_item
                sales_order_item.save()

                new_item_doc = frappe.get_doc("Item", new_item)
                new_item_doc.status = "Rented Out"
                new_item_doc.save()
            else:
                sales_order_item = frappe.get_doc("Sales Order Item", item.name)
                sales_order_item.child_status = item.child_status
                sales_order_item.replaced_datetime = replacement_date
                sales_order_item.old_item_code = item_code
                sales_order_item.item_code = new_item
                sales_order_item.save()

                new_item_doc = frappe.get_doc("Item", new_item)
                new_item_doc.status = "Reserved"
                new_item_doc.save()

        # Update the status of the old item
        old_item_doc = frappe.get_doc("Item", item_code)
        old_item_doc.status = old_item_status
        old_item_doc.replaced_reason = reason
        old_item_doc.save()

        # Update sales order status to "Active"
        sales_order_items_status = frappe.get_all("Sales Order Item", filters={"parent": docname}, fields=["name", "child_status"])
        if any(item.child_status != "Ready for Delivery" and item.child_status != "DISPATCHED" for item in sales_order_items_status):
            all_active = all(item.child_status == "Active" for item in sales_order_items_status)
            any_submitted = any(item.child_status == "Submitted to Office" for item in sales_order_items_status)
            not_submitted = any(item.child_status != "Submitted to Office" for item in sales_order_items_status)

            # Update sales order status
            sales_order_replace = frappe.get_doc("Sales Order", docname)
            if all_active:
                sales_order_replace.status = "Active"
            elif any_submitted:
                sales_order_replace.status = "Partially Closed"
            elif not_submitted:
                sales_order_replace.status = "Active"  # Handle the case when neither condition is met
            sales_order_replace.save()

        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Item Replacement Failed"))
        frappe.throw(_("Item Replacement Failed. Please try again later."))

import frappe
from frappe import _

# Define the server-side method to fetch replaced items
@frappe.whitelist()
def get_replaced_items(master_order_id):
    try:
        # Fetch replaced items associated with the sales order
        replaced_items = frappe.get_all("Rental Order Replaced Item",
                                        filters={"master_order_id": master_order_id},
                                        fields=["old_item", "new_item", "replaced_datetime", "reason"])
        return replaced_items
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to fetch replaced items"))
        return None




@frappe.whitelist()
def get_journal_entry_records(master_order_id):
    try:
        # Fetch replaced items associated with the sales order
        journal_entry_records = frappe.get_all("Journal Entry",
                                        filters={"master_order_id": master_order_id},
                                        fields=["name", "sales_order_id", "master_order_id", "security_deposite_type","total_debit","posting_date"])

        # Iterate through each journal entry record
        for entry in journal_entry_records:
            # Fetch accounts associated with the current journal entry
            accounts = frappe.get_all("Journal Entry Account",
                                       filters={"parent": entry["name"]},
                                       fields=["account", "debit_in_account_currency", "credit_in_account_currency"])

            # Add accounts data to the journal entry record
            entry["accounts"] = accounts

        return journal_entry_records
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to fetch replaced items"))
        return None


@frappe.whitelist()
def get_payment_entry_records(master_order_id):
    try:
        # Fetch replaced items associated with the sales order
        payment_entry_records = frappe.get_all("Payment Entry",
                                        filters={"master_order_id": master_order_id},
                                        fields=["name", "references.reference_name", "master_order_id","total_allocated_amount","posting_date"])
        return payment_entry_records
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to fetch replaced items"))
        return None


# Method to delete journal entry
import frappe
@frappe.whitelist()
def cancel_and_delete_journal_entry(journal_entry_id):
    # Get the journal entry
    journal_entry = frappe.get_doc("Journal Entry", journal_entry_id)

    # Check if the journal entry is submitted
    if journal_entry.docstatus == 1:
        # Cancel the journal entry
        journal_entry.cancel()

        # Commit the changes
        frappe.db.commit()

        # Delete the journal entry
        frappe.delete_doc("Journal Entry", journal_entry_id)

        # Commit the deletion
        frappe.db.commit()

        return True, "Journal entry cancelled and deleted successfully."
    else:
        return False, "Journal entry is not submitted."



@frappe.whitelist()
def cancel_and_delete_payment_entry(payment_entry_id):
    # Get the journal entry
    payment_entry = frappe.get_doc("Payment Entry", payment_entry_id)

    # Check if the journal entry is submitted
    if payment_entry.docstatus == 1:
        # Cancel the journal entry
        payment_entry.cancel()

        # Commit the changes
        frappe.db.commit()

        # Delete the journal entry
        frappe.delete_doc("Payment Entry", payment_entry_id)

        # Commit the deletion
        frappe.db.commit()

        return True, "Journal entry cancelled and deleted successfully."
    else:
        return False, "Journal entry is not submitted."




@frappe.whitelist()
def process_payment(balance_amount, outstanding_security_deposit_amount, customer_name, rental_payment_amount, sales_order_name, master_order_id, security_deposit_status, customer, payment_account=None, security_deposit_account=None, reference_no=None, reference_date=None, mode_of_payment=None,
                    security_deposit_payment_amount=None, remark=None):
    try:
        # Convert balance_amount and outstanding_security_deposit_amount to floats
        balance_amount = float(balance_amount)
        outstanding_security_deposit_amount = float(outstanding_security_deposit_amount)

        # Check if rental_payment_amount and security_deposit_payment_amount are not negative
        if float(rental_payment_amount) < 0 or float(security_deposit_payment_amount) < 0:
            frappe.throw("Payment amounts cannot be negative.")
            return False

        # Check if balance_amount and outstanding_security_deposit_amount are not negative
        if balance_amount < 0 or outstanding_security_deposit_amount < 0:
            frappe.throw("Balance amounts cannot be negative.")
            return False

        # Convert rental_payment_amount to a float
        rental_payment_amount = float(rental_payment_amount) if rental_payment_amount else 0
        security_deposit_payment_amount = float(security_deposit_payment_amount) if security_deposit_payment_amount else 0

        # Check if security_deposit_payment_amount and rental_payment_amount are greater than 0
        if security_deposit_payment_amount > 0 and rental_payment_amount > 0:
            # Check if security_deposit_payment_amount is greater than outstanding_security_deposit_amount
            if security_deposit_payment_amount > outstanding_security_deposit_amount:
                # Show an alert if security_deposit_payment_amount is greater
                frappe.throw("Security Deposit Payment Amount cannot be greater than the Security Deposit Amount.")
                return False
            
            # Check if rental_payment_amount is greater than balance_amount
            if rental_payment_amount > balance_amount:
                # Show an alert if rental_payment_amount is greater
                frappe.throw("Rental Payment Amount cannot be greater than the Balance Amount.")
                return False

            # Create a journal entry for the security deposit payment amount
            create_security_deposit_journal_entry_payment(customer_name, security_deposit_payment_amount, sales_order_name, master_order_id, security_deposit_account, reference_no, reference_date, remark)
            
            # Create a payment entry for the rental payment amount
            create_rental_payment_entry(customer_name, rental_payment_amount, mode_of_payment, sales_order_name, security_deposit_status, customer, payment_account, master_order_id, reference_no, reference_date, remark)
            
            return True

        elif security_deposit_payment_amount > 0:
            # Check if security_deposit_payment_amount is greater than outstanding_security_deposit_amount
            if security_deposit_payment_amount > outstanding_security_deposit_amount:
                # Show an alert if security_deposit_payment_amount is greater
                frappe.throw("Security Deposit Payment Amount cannot be greater than the Security Deposit Amount.")
                return False

            # Create a journal entry for the security deposit payment amount
            create_security_deposit_journal_entry_payment(customer_name, security_deposit_payment_amount, sales_order_name, master_order_id, security_deposit_account, reference_no, reference_date, remark)
            return True
        
        elif rental_payment_amount > 0:
            # Check if rental_payment_amount is greater than balance_amount
            if rental_payment_amount > balance_amount:
                # Show an alert if rental_payment_amount is greater
                frappe.throw("Rental Payment Amount cannot be greater than the Balance Amount.")
                return False
	
            # Create a payment entry for the rental payment amount
            create_rental_payment_entry(customer_name, rental_payment_amount, mode_of_payment, sales_order_name, security_deposit_status, customer, payment_account, master_order_id, reference_no, reference_date, remark)
            return True


    except Exception as e:
        error_message = f"Failed to process payment: {str(e)}"
        frappe.log_error(frappe.get_traceback(), error_message)
        frappe.throw(error_message)

    return False


def create_security_deposit_journal_entry_payment(customer, security_deposit_payment_amount, sales_order_name, master_order_id, security_deposit_account, reference_no=None, reference_date=None, remark=None):
    try:
        # Create a new Journal Entry document
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.voucher_type = "Journal Entry"
        journal_entry.sales_order_id = sales_order_name
        journal_entry.posting_date = frappe.utils.nowdate()
        journal_entry.journal_entry_type = "Security Deposit"
        journal_entry.security_deposite_type = "Cash Received From Client"
        journal_entry.master_order_id = master_order_id
        journal_entry.cheque_no = reference_no
        journal_entry.cheque_date = reference_date
        journal_entry.user_remark = remark

        # Add accounts for debit and credit
        journal_entry.append("accounts", {
            "account": security_deposit_account,
            "debit_in_account_currency": security_deposit_payment_amount
        })
        journal_entry.append("accounts", {
            "account": "Rental Order Security Deposit Receivable - INR",
            "party_type": "Customer",
            "party": customer,
            "credit_in_account_currency": security_deposit_payment_amount
        })

        # Save and submit the Journal Entry document
        journal_entry.insert()
        journal_entry.submit()

        frappe.msgprint("Security Deposit Journal Entry created successfully.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to create Security Deposit Journal Entry"))
        frappe.throw(_("Failed to create Security Deposit Journal Entry. Please try again later."))


def create_rental_payment_entry(customer_name, rental_payment_amount, mode_of_payment,
                                sales_order_name, security_deposit_status, customer, payment_account, master_order_id, reference_no=None, reference_date=None, remark=None):
    try:
        rental_payment_amount_numeric = float(rental_payment_amount)  # Convert rental_payment_amount to float

        # Create a new Payment Entry document
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "master_order_id": master_order_id,
            "paid_from": "Debtors - INR",
            "received_amount": rental_payment_amount_numeric,
            "base_received_amount": rental_payment_amount_numeric,  # Assuming base currency is INR
            "received_amount_currency": "INR",
            "base_received_amount_currency": "INR",
            "target_exchange_rate": 1,
            "paid_amount": rental_payment_amount_numeric,
            "references": [
                {
                    "reference_doctype": "Sales Order",
                    "reference_name": sales_order_name,
                    "allocated_amount": rental_payment_amount_numeric
                }
            ],
            "reference_date": reference_date,
            "party_type": "Customer",
            "party": customer,
            "mode_of_payment": mode_of_payment,
            "reference_no": reference_no,
            "paid_to": payment_account,
            "payment_remark": remark,
        }, ignore_permissions=True)

        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()

        frappe.msgprint("Payment Entry created successfully.")

        frappe.log_error("Rental Payment Entry created successfully.", _("Rental Payment Entry"))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to create Rental Payment Entry"))
        frappe.throw(_("Failed to create Rental Payment Entry. Please try again later. Error: {0}".format(str(e))))


@frappe.whitelist()
def get_default_account(mode_of_payment):
    try:
        # Fetch the Mode Of Payment document
        mode_of_payment_doc = frappe.get_doc("Mode of Payment", mode_of_payment)

        # Initialize default_account and journal_entry_default_account
        default_account = None
        journal_entry_default_account = mode_of_payment_doc.journal_entry_default_account

        # Iterate through the child table entries
        for account in mode_of_payment_doc.get("accounts"):
            if account.default_account:
                default_account = account.default_account
                break

        if default_account:
            return {"default_account": default_account, "journal_entry_default_account": journal_entry_default_account}
        else:
            # Return "Bank Account - INR" if default account not found
            return {"default_account": "Bank Account - INR","journal_entry_default_account": "Kotak Bank Security Deposit Received - INR"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to fetch default account"))
        frappe.throw(_("Failed to fetch default account. Please try again later."))




@frappe.whitelist()
def return_security_deposit(amount_to_return, journal_entry_account, master_order_id, sales_order_id, customer):
    try:
        # Create a journal entry to return the security deposit amount
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "posting_date": frappe.utils.today(),
            "company": frappe.defaults.get_user_default("company"),
            "accounts": [
                {
                    "account": "Debtors - INR",
                    "debit_in_account_currency": amount_to_return,
					"party_type":"Customer",
					"party":customer,
                    "credit_in_account_currency": 0,
                    # "cost_center": frappe.defaults.get_user_default("cost_center")
                },
                {
                    "account": journal_entry_account,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": amount_to_return,
                    "party_type": "Customer",
                    "party": customer,
                    # "cost_center": frappe.defaults.get_user_default("cost_center")
                }
            ],
            "remarks": f"Return Security Deposit for Sales Order {sales_order_id}",
            "master_order_id": master_order_id,
            "sales_order_id": sales_order_id,
			"journal_entry_type":"Security Deposit",
			"security_deposite_type":"Return to Client"
        })

        # Save the journal entry
        journal_entry.insert()
        journal_entry.submit()

        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Failed to create journal entry"))
        return False
