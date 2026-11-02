<!-- DataTable.vue -->

<script setup lang="ts">
export interface DataTableColumn {
  key: string;
  label: string;
  align?: "left" | "right";
  width?: string;
}

const props = withDefaults(defineProps<{
  columns: DataTableColumn[];
  rows?: any[];
  loading?: boolean;
  emptyMessage?: string;
  rowLink?: (row: any) => string;
}>(), {
  rows: () => [],
  loading: false,
  emptyMessage: "Nothing here yet.",
});
</script>

<template>
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th
            v-for="c in columns"
            :key="c.key"
            :style="{ textAlign: c.align ?? 'left', width: c.width }"
          >{{ c.label }}</th>
        </tr>
      </thead>

      
<tbody>
  <tr v-if="loading">
    <td :colspan="columns.length" class="table__msg">Loading…</td>
  </tr>

  <tr v-else-if="!rows?.length">
    <td :colspan="columns.length" class="table__msg">
      {{ emptyMessage ?? "Nothing here yet." }}
    </td>
  </tr>

  <tr
    v-else
    v-for="row in rows"
    :key="row.id"
    :class="{ 'clickable-row': !!rowLink }"
    @click="rowLink && $router.push(rowLink(row))"
  >
    <td
      v-for="c in columns"
      :key="c.key"
      :style="{ textAlign: c.align ?? 'left' }"
    >
      <slot :name="c.key" :row="row">
        {{ row[c.key] ?? "—" }}
      </slot>
    </td>
  </tr>
</tbody>


    </table>
  </div>
</template>

<style scoped>
.table-wrap { background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-soft); overflow: hidden; }
.table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
.table th {
  padding: var(--sp-3) var(--sp-4);
  text-align: left;
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-gold);
  background: var(--color-ivory);
  border-bottom: 1px solid var(--color-border-soft);
}
.table td {
  padding: var(--sp-3) var(--sp-4);
  border-bottom: 1px solid var(--color-border-soft);
  color: var(--color-text);
  vertical-align: middle;
}
.table tbody tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: rgba(201, 164, 92, 0.04); }
.table__msg { padding: var(--sp-6); text-align: center; color: var(--color-text-muted); }
.clickable-row {
  cursor: pointer;
}

.clickable-row:hover {
  background: rgba(201, 164, 92, 0.1);
}
</style>