<template>
	<div>
		<div>
			<ListManager v-if="listManagerInitialised" class="px-[16px]" ref="contactList" :options="{
				cache: ['Contacts', 'Desk'],
				doctype: 'Contact',
				fields: [
					'first_name',
					'last_name',
					'email_ids.email_id as email',
					'phone_nos.phone as phone',
					'organization',
				],
				limit: 40,
			}">
				<template #body="{ manager }">
					<div>
						<div class="flow-root py-4 px-[16px]">
							<div class="float-left"></div>
							<div class="float-right">
								<div class="flex items-center space-x-3">
									<div>
										<FilterBox class="mt-6" v-if="toggleFilters" @close="
											() => {
												toggleFilters = false
											}
										" :options="filterBoxOptions()" v-model="filters" />
									</div>
									<div class="stroke-blue-500 fill-blue-500 w-0 h-0 block"></div>
									<Button :class="
										Object.keys(filters).length == 0
											? 'bg-gray-100 text-gray-600'
											: 'bg-blue-100 text-blue-500 hover:bg-blue-300'
									" @click="() => { toggleFilters = !toggleFilters }" v-if="!Object.keys(manager.selectedItems).length > 0">
										<div class="flex items-center space-x-2">
											<CustomIcons height="18" width="18" name="filter" :class="
												Object.keys(filters).length > 0
													? 'stroke-blue-500 fill-blue-500'
													: 'stroke-black'
											" />
											<div>Add Filters</div>
											<div class="bg-blue-500 text-white px-1.5 rounded" v-if="
												Object.keys(filters).length > 0
											">
												{{
														Object.keys(this.filters).length
												}}
											</div>
										</div>
									</Button>
									<Button v-if="Object.keys(manager.selectedItems).length > 0" appearance="danger"
										@click="deleteSelectedContacts(Object.keys(manager.selectedItems))">Delete
										Contact</Button>
									<Button v-else icon-left="plus" appearance="primary" @click="
										() => {
											showNewContactDialog = true
										}
									">Add Contact</Button>
								</div>
							</div>
						</div>
						<ContactList :manager="manager" />
					</div>
				</template>
			</ListManager>
		</div>
		<NewContactDialog v-model="showNewContactDialog" @contact-created="() => {
	showNewContactDialog = false
}
		" />
	</div>
</template>
<script>
import ListManager from "@/components/global/ListManager.vue"
import ContactList from "../../components/desk/contacts/ContactList.vue"
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue"
import FilterBox from "@/components/desk/global/FilterBox.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { inject, ref } from "vue"
import { BubbleMenu } from "@tiptap/vue-3"
import { Dropdown } from "frappe-ui"

export default {
	name: "Contacts",
	components: {
		ListManager,
		NewContactDialog,
		ContactList,
		BubbleMenu,
		Dropdown,
		FilterBox,
		CustomIcons,

	},
	data() {
		return {
			initialFilters: [],
		}
	},
	setup() {
		const showNewContactDialog = ref(false)
		const filters = ref([])
		const toggleFilters = ref(false)
		const listManagerInitialised = ref(false)

		const contactName = inject("contactName")
		const contactEmail = inject("contactEmail")
		const contactOrganization = inject("contactOrganization")

		return {
			showNewContactDialog,
			listManagerInitialised,
			filters,
			toggleFilters,
			contactName,
			contactEmail,
			contactOrganization,
		}
	},
	computed: {
		contacts() {
			return this.contacts || null
		},
	},
	mounted() {
		if (this.$route.query) {
			for (const [key, value] of Object.entries(this.$route.query)) {
				if (
					[
						"name",
						"email_id",
						"organization",
					].includes(key)
				) {
					const filter = {}
					filter[key] = value
					this.filters.push(filter)
				}
			}
		}
		this.applyFiltersToList()
	},
	watch: {
		filters(newValue) {
			let query = {}

			newValue.forEach((filter) => {
				for (const [key, value] of Object.entries(filter)) {
					if (
						[
							"name",
							"email_id",
							"organization",
						].includes(key)
					) {
						query[key] = value
					}
				}
			})
			this.$router.push({ path: this.$route.path, query })
		},
		$route() {
			this.applyFiltersToList()
			if (this.$route.name === "Contact") {
				this.applyFiltersToList()
			}
		},
	},
	methods: {
		deleteSelectedContacts(items) {
			this.$resources.bulk_delete_contacts.submit({
				items: items,
				doctype: "Contact",
			})
		},
		applyFiltersToList() {
			const finalFilters = {}

			this.filters.forEach((filter) => {
				for (const [key, value] of Object.entries(filter)) {
					finalFilters[key] = ["=", value]
				}
			})
			// TODO: move this to filter box
			if (this.listManagerInitialised) {
				if (
					JSON.stringify(finalFilters) !=
					JSON.stringify(
						this.$refs.contactList.manager.options.filters
					)
				) {
					this.$refs.contactList.manager.update({
						filters: finalFilters,
					})
				}
			} else {
				this.initialFilters = finalFilters
				this.listManagerInitialised = true
			}
		},
		filterBoxOptions() {
			return [
				{
					label: "Name",
					name: "name",
					items: this.contactName.map((item) => item.name),
				},
				{
					label: "Email",
					name: "email_id",
					items: this.contactEmail,
				},
				{
					label: "Organization",
					name: "organization",
					items: this.contactOrganization,
				},
				// TODO: {label: "Created On", name: "creation", type: 'calander'}
			]
		},
	},
	resources: {
		bulk_delete_contacts() {
			return {
				method: "frappedesk.api.doc.delete_items",
				onSuccess: () => {
					this.$router.go()
				},
				onError: (err) => {
					this.$refs.listManager.manager.reload()
					this.$toast({
						title: "Error while deleting contacts",
						text: err,
						customIcon: "circle-check",
						appearance: "success",
					})
				},
			}
		},
	},


}
</script>
