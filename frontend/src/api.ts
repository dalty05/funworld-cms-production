// api.ts

import axios, { AxiosError, type AxiosRequestConfig } from "axios";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export const http = axios.create({
  baseURL: API_BASE,
  timeout: 20_000,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT if present (admin routes)
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("fw_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Let the browser/Axios set the multipart boundary for file uploads.
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    config.headers.delete("Content-Type");
  }

  return config;
});

// Standard error envelope → typed error
export interface ApiErrorShape {
  error: { code: string; message: string; details?: Record<string, unknown> };
  meta?: { request_id?: string; timestamp?: string };
}

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;
  status: number;
  constructor(shape: ApiErrorShape, status: number) {
    super(shape.error.message);
    this.code = shape.error.code;
    this.details = shape.error.details ?? {};
    this.status = status;
  }
}

http.interceptors.response.use(
  (r) => r,
  (err: AxiosError<ApiErrorShape>) => {
    if (err.response?.data?.error) {
      throw new ApiError(err.response.data, err.response.status);
    }
    throw err;
  }
);


let _redirectingToLogin = false;

function redirectToLogin() {
  if (_redirectingToLogin) return;
  _redirectingToLogin = true;

  localStorage.removeItem("fw_token");
  localStorage.removeItem("fw_refresh");

  const current = window.location.pathname + window.location.search;
  if (!current.startsWith("/admin/login")) {
    const next = encodeURIComponent(current);
    window.location.href = `/admin/login?next=${next}`;
  } else {
    _redirectingToLogin = false;
  }
}

http.interceptors.response.use(
  (r) => r,
  (err: AxiosError<ApiErrorShape>) => {
    const status = err.response?.status;

    // Session expired / invalid token → kick to login
    if (status === 401) {
      redirectToLogin();
      throw new ApiError(
        err.response?.data ?? {
          error: { code: "unauthorized", message: "Session expired." },
        },
        status
      );
    }

    if (err.response?.data?.error) {
      throw new ApiError(err.response.data, err.response.status);
    }
    throw err;
  }
);





// ─── Public endpoints ────────────────────────────────────────────

export interface WhatsAppLinkResponse {
  data: { link: string };
}

export async function getWhatsAppLink(params: {
  kind: "package" | "service" | "custom";
  name?: string;
  text?: string;
  ref?: string;
}): Promise<string> {
  const { data } = await http.get<WhatsAppLinkResponse>("/whatsapp/link", { params });
  return data.data.link;
}

export interface EnquiryCreatePayload {
  customer: { full_name: string; phone?: string; email?: string };
  channel: string;
  event_type?: string;
  event_date?: string;
  venue?: string;
  guest_count?: number;
  services_interested?: Record<string, unknown>;
  budget_indication?: string;
  notes?: string;
  // Phase 12 attribution
  source_page?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referrer_url?: string;
  package_id?: string;
}

export async function submitEnquiry(payload: EnquiryCreatePayload, idempotencyKey: string) {
  const { data } = await http.post("/enquiries", payload, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
  return data;
}

export interface ContactMessagePayload {
  full_name: string;
  email?: string;
  phone?: string;
  subject?: string;
  message: string;
}

export async function submitContactMessage(payload: ContactMessagePayload, idempotencyKey: string) {
  const { data } = await http.post("/contact-messages", payload, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
  return data;
}

// ─── Catalogue (packages/services served by the backend) ─────────

export interface PackageSummary {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  short_description: string | null;
  price_amount: number | null;
  price_note: string | null;
  currency: string;
  hero_image_url: string | null;
  is_featured: boolean;
  availability_note: string | null;
  duration_hours: number | null;
  min_guests: number | null;
  max_guests: number | null;
  category: {
    slug: string;
    name: string;
  } | null;
}

export async function listPackages(): Promise<PackageSummary[]> {
  const { data } = await http.get("/packages");
  return data.data;
}

export async function getPackage(slug: string) {
  const { data } = await http.get(`/packages/${slug}`);
  return data.data;
}

export interface BlogPostSummary {
  slug: string;
  title: string;
  excerpt: string;
  featured_image: string | null;
  published_at: string;
  author: { full_name: string } | null;
  categories: { slug: string; name: string }[];
}

export async function listBlogPosts(params: { limit?: number; category?: string } = {}) {
  const { data } = await http.get<{ data: BlogPostSummary[] }>("/blog", { params });
  return data.data;
}

export async function getBlogPost(slug: string) {
  const { data } = await http.get(`/blog/${slug}`);
  return data.data;
}





// ─── Users & permissions ─────────────────────────────────────────

export async function listUsers() {
  const { data } = await http.get("/users");
  return data.data;
}

export async function listPermissions() {
  const { data } = await http.get("/permissions");
  return data.data;
}

export async function listRoles() {
  const { data } = await http.get("/roles");
  return data.data;
}

export async function updateRole(id: string, payload: any) {
  const { data } = await http.patch(`/roles/${id}`, payload);
  return data.data;
}







// ─── Inventory ───────────────────────────────────────────────────────

export interface InventoryCategory {
  id: string;
  slug: string;
  name: string;
  short_description: string | null;
  icon: string | null;
  sort_order: number;
  item_count: number;
}

export interface InventoryItem {
  id: string;
  category_id: string;
  category_slug?: string;
  slug: string;
  name: string;
  short_description: string | null;
  long_description?: string | null;
  quantity_owned: number;
  quantity_available_note: string | null;
  unit_price_hint: number | null;
  unit: string | null;
  currency: string;
  featured_image_url: string | null;
  gallery?: string[];
  tags?: string[];
  is_published: boolean;
  sort_order: number;
}

export async function listInventoryCategories(): Promise<InventoryCategory[]> {
  const { data } = await http.get("/admin/inventory/categories");
  return data.data;
}

export async function createInventoryCategory(payload: any) {
  const { data } = await http.post("/admin/inventory/categories", payload, {
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
  return data.data;
}

export async function listInventory(params: Record<string, string | number> = {}): Promise<InventoryItem[]> {
  const { data } = await http.get("/admin/inventory", { params });
  return data.data;
}

export async function getInventoryItem(itemId: string): Promise<InventoryItem> {
  const { data } = await http.get(`/admin/inventory/${itemId}`);
  return data.data;
}

export async function createInventoryItem(payload: any) {
  const { data } = await http.post("/admin/inventory", payload, {
    headers: { "Idempotency-Key": crypto.randomUUID() },
  });
  return data.data;
}

export async function updateInventoryItem(itemId: string, payload: any) {
  const { data } = await http.patch(`/admin/inventory/${itemId}`, payload);
  return data.data;
}

export async function publishInventoryItem(itemId: string) {
  const { data } = await http.post(`/admin/inventory/${itemId}/publish`);
  return data.data;
}

export async function unpublishInventoryItem(itemId: string) {
  const { data } = await http.post(`/admin/inventory/${itemId}/unpublish`);
  return data.data;
}

export async function deleteInventoryItem(itemId: string) {
  const { data } = await http.delete(`/admin/inventory/${itemId}`);
  return data.data;
}

export async function replacePackageInventory(
  packageId: string,
  items: { inventory_item_id: string; quantity: number; notes?: string }[],
) {
  const { data } = await http.put(
    `/admin/packages/${packageId}/inventory`,
    { items },
    { headers: { "Idempotency-Key": crypto.randomUUID() } },
  );
  return data.data;
}








// ─── Public settings ─────────────────────────────────────────────
export type PublicSettings = Record<string, string | null>;

export async function getPublicSettings(): Promise<PublicSettings> {
  const { data } = await http.get("/settings/public");
  return data?.data ?? {};
}

// ─── Service categories ──────────────────────────────────────────
export type ServiceCategorySummary = {
  slug: string;
  name: string;
  short_description: string | null;
  hero_image_url: string | null;
  accent_color: string | null;
  service_count: number;
};

export async function listServiceCategories(): Promise<ServiceCategorySummary[]> {
  const { data } = await http.get("/services/categories");
  return data?.data ?? [];
}

// ─── Featured gallery (for hero) ─────────────────────────────────
export type GalleryImage = {
  id: string;
  url: string;
  thumb_url: string;
  alt_text: string;
  caption: string | null;
  width: number | null;
  height: number | null;
  is_featured: boolean;
};

export async function listFeaturedGallery(limit = 5): Promise<GalleryImage[]> {
  const { data } = await http.get("/gallery", {
    params: { featured: "true", limit },
  });
  return data?.data ?? [];
}

// ─── Rentals strip ───────────────────────────────────────────────
export type RentalCategory = {
  slug: string;
  name: string;
  short_description: string | null;
  published_item_count: number;
};

export async function listRentalCategories(): Promise<RentalCategory[]> {
  const { data } = await http.get("/rentals");
  return data?.data ?? [];
}



// // ─── Rental items within a category ─────────────────────────────
// export type RentalItem = {
//   id: string;
//   slug: string;
//   name: string;
//   short_description: string | null;
//   featured_image_url: string | null;
//   gallery: string[];
//   tags: string[];
//   from_price: number | null;
//   unit: string | null;
//   currency: string;
//   availability_note: string | null;
//   category: { slug: string; name: string } | null;
//   wa_link: string | null;
// };

export type RentalCategoryDetail = {
  slug: string;
  name: string;
  short_description: string | null;
  long_description: string | null;
  icon: string | null;
};

export async function listRentalItems(categorySlug: string): Promise<{
  items: RentalItem[];
  category: RentalCategoryDetail | null;
}> {
  const { data } = await http.get("/rentals", {
    params: { category: categorySlug },
  });
  return {
    items: data?.data ?? [],
    category: data?.meta?.category ?? null,
  };
}



// ─── All published rental items (for hero & featured strips) ────
export type RentalItem = {
  id: string;
  slug: string;
  name: string;
  short_description: string | null;
  featured_image_url: string | null;
  gallery: string[];
  tags: string[];
  from_price: number | null;
  unit: string | null;
  currency: string;
  availability_note: string | null;
  category: { slug: string; name: string } | null;
  wa_link: string | null;
};

export async function listRentals(): Promise<RentalItem[]> {
  // Fetch categories, then the first 2 items from each (breadth-first).
  // This is light enough for the hero and doesn't require a new backend route.
  const { data: catData } = await http.get("/rentals");
  const cats: { slug: string }[] = catData?.data ?? [];
  if (!cats.length) return [];

  const categoryResults = await Promise.all(
    cats.slice(0, 4).map((c) =>
      http.get("/rentals", { params: { category: c.slug } })
    )
  );

  const items: RentalItem[] = [];
  for (const r of categoryResults) {
    const rows: RentalItem[] = r.data?.data ?? [];
    items.push(...rows.slice(0, 2));
  }
  return items;
}




