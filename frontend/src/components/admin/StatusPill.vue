<script setup lang="ts">
defineProps<{ status: string; kind?: "enquiry" | "booking" | "quote" | "invoice" | "post" }>();

const COLOR_MAP: Record<string, string> = {
  unverified: "gray",
  qualified: "blue",
  quoted: "amber",
  converted: "green",
  lost: "red",
  archived: "gray",

  draft: "gray",
  pending: "amber",
  awaiting_payment: "amber",
  committed: "blue",
  confirmed: "green",
  in_progress: "blue",
  completed: "green",
  cancelled: "red",
  expired: "red",

  sent: "blue",
  failed: "red",
  dead: "red",
  viewed: "blue",
  negotiating: "amber",
  accepted: "green",
  rejected: "red",
  void: "gray",

  partially_paid: "amber",
  paid: "green",
  overdue: "red",

  review: "amber",
  scheduled: "blue",
  published: "green",
};
</script>

<template>
  <span class="pill" :class="`pill--${COLOR_MAP[status] ?? 'gray'}`">
    {{ status.replace(/_/g, " ") }}
  </span>
</template>

<style scoped>
.pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-xs);
  font-weight: 600;
  text-transform: capitalize;
  letter-spacing: 0.02em;
}
.pill--gray { background: #E5E7EB; color: #4B5563; }
.pill--amber { background: #FEF3C7; color: #92400E; }
.pill--blue { background: #DBEAFE; color: #1E40AF; }
.pill--green { background: #D1FAE5; color: #065F46; }
.pill--red { background: #FEE2E2; color: #991B1B; }
</style>