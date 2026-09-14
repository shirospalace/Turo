const MARKETPLACES = ["amazon", "ebay", "etsy"];

const state = {
  categories: [],
  feeConfigs: [],
  products: [],
  selectedProductId: null,
  integrationStatus: {},
};

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch (e) {}
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function money(n) {
  return `$${(n ?? 0).toFixed(2)}`;
}

// ---------- Tabs ----------
function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
      if (btn.dataset.tab === "orders") loadOrders();
      if (btn.dataset.tab === "summary") loadSummary();
      if (btn.dataset.tab === "listings") refreshListingProductOptions();
    });
  });
}

// ---------- Categories ----------
async function loadCategories() {
  state.categories = await api("/api/categories");
  const opts = state.categories.map((c) => `<option value="${c.id}">${c.name}</option>`).join("");
  document.getElementById("p_category").innerHTML = opts;
  document.getElementById("csv_category").innerHTML = opts;
}

// ---------- Integrations / Settings modal ----------
async function loadIntegrationStatus() {
  state.integrationStatus = await api("/api/integrations/status");
  const badges = Object.entries(state.integrationStatus)
    .map(([name, info]) => `<span class="badge ${info.configured ? "ok" : "off"}">${name}: ${info.configured ? "connected" : "not connected"}</span>`)
    .join("");
  document.getElementById("integrationBadges").innerHTML = badges;

  const container = document.getElementById("integrationStatusContainer");
  container.innerHTML = Object.entries(state.integrationStatus)
    .map(
      ([name, info]) =>
        `<p><strong>${name}</strong>: ${info.configured ? "connected" : "not connected"} — ${info.requires}</p>`
    )
    .join("");
}

async function loadFeeConfigs() {
  state.feeConfigs = await api("/api/fee-configs");
  const container = document.getElementById("feeConfigsContainer");
  container.innerHTML = state.feeConfigs
    .map(
      (cfg) => `
    <div class="fee-row" data-marketplace="${cfg.marketplace}">
      <div><strong>${cfg.marketplace}</strong></div>
      <label>Listing fee $ <input type="number" step="0.01" class="fc_listing_fee" value="${cfg.listing_fee}"></label>
      <label>Variable % 1 <input type="number" step="0.01" class="fc_variable_pct_1" value="${cfg.variable_pct_1}"></label>
      <label>Fixed fee 1 $ <input type="number" step="0.01" class="fc_fixed_fee_1" value="${cfg.fixed_fee_1}"></label>
      <label>Variable % 2 <input type="number" step="0.01" class="fc_variable_pct_2" value="${cfg.variable_pct_2}"></label>
      <label>Fixed fee 2 $ <input type="number" step="0.01" class="fc_fixed_fee_2" value="${cfg.fixed_fee_2}"></label>
      <button class="btn-primary fc_save" type="button">Save</button>
    </div>`
    )
    .join("");

  container.querySelectorAll(".fc_save").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const row = btn.closest(".fee-row");
      const marketplace = row.dataset.marketplace;
      const payload = {
        listing_fee: parseFloat(row.querySelector(".fc_listing_fee").value) || 0,
        variable_pct_1: parseFloat(row.querySelector(".fc_variable_pct_1").value) || 0,
        fixed_fee_1: parseFloat(row.querySelector(".fc_fixed_fee_1").value) || 0,
        variable_pct_2: parseFloat(row.querySelector(".fc_variable_pct_2").value) || 0,
        fixed_fee_2: parseFloat(row.querySelector(".fc_fixed_fee_2").value) || 0,
        notes: "",
      };
      await api(`/api/fee-configs/${marketplace}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      await loadProducts();
      renderProductsTable();
    });
  });
}

function setupSettingsModal() {
  document.getElementById("settingsBtn").addEventListener("click", () => {
    document.getElementById("settingsModal").classList.remove("hidden");
  });
  document.getElementById("closeSettings").addEventListener("click", () => {
    document.getElementById("settingsModal").classList.add("hidden");
  });
}

// ---------- Products / margin table ----------
async function loadProducts() {
  const threshold = parseFloat(document.getElementById("marginThreshold").value) || 20;
  state.products = await api(`/api/products?margin_threshold=${threshold}`);
}

function marginCell(product, marketplace) {
  const lp = product.listing_prices.find((l) => l.marketplace === marketplace) || {
    target_sale_price: 0,
    shipping_cost_estimate: 0,
  };
  const m = product.margins.find((mm) => mm.marketplace === marketplace);
  const marginClass = m && m.below_threshold ? "flag-low" : "";
  return `
    <td><input type="number" step="0.01" class="price-input" data-product="${product.id}" data-marketplace="${marketplace}" value="${lp.target_sale_price}" style="width:70px"></td>
    <td class="${marginClass}">${m ? m.margin_pct.toFixed(1) + "%" : "-"}</td>
    <td class="${marginClass}">${m ? money(m.net_profit) : "-"}</td>
  `;
}

function renderProductsTable() {
  const tbody = document.getElementById("productsTableBody");
  tbody.innerHTML = state.products
    .map(
      (p) => `
    <tr class="clickable" data-product-id="${p.id}">
      <td>${p.title}</td>
      <td>${p.category_name}</td>
      <td>${money(p.cost)}</td>
      <td>${p.warehouse_location}</td>
      <td>${p.est_ship_days || "-"}d</td>
      <td>${p.status}</td>
      ${marginCell(p, "amazon")}
      ${marginCell(p, "ebay")}
      ${marginCell(p, "etsy")}
      <td><button class="btn-danger del-product" data-id="${p.id}" type="button">Delete</button></td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll(".price-input").forEach((input) => {
    input.addEventListener("click", (e) => e.stopPropagation());
    input.addEventListener("change", async (e) => {
      e.stopPropagation();
      const productId = input.dataset.product;
      const marketplace = input.dataset.marketplace;
      const product = state.products.find((p) => p.id == productId);
      const lp = product.listing_prices.find((l) => l.marketplace === marketplace) || { shipping_cost_estimate: 0 };
      await api(`/api/products/${productId}/listing-price`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          marketplace,
          target_sale_price: parseFloat(input.value) || 0,
          shipping_cost_estimate: lp.shipping_cost_estimate || 0,
        }),
      });
      await loadProducts();
      renderProductsTable();
    });
  });

  tbody.querySelectorAll(".del-product").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this product?")) return;
      await api(`/api/products/${btn.dataset.id}`, { method: "DELETE" });
      await loadProducts();
      renderProductsTable();
    });
  });

  tbody.querySelectorAll("tr[data-product-id]").forEach((row) => {
    row.addEventListener("click", () => selectProduct(parseInt(row.dataset.productId)));
  });
}

function setupProductForm() {
  const form = document.getElementById("productForm");
  document.getElementById("toggleAddForm").addEventListener("click", () => {
    form.classList.toggle("hidden");
    if (!form.classList.contains("hidden")) resetProductForm();
  });
  document.getElementById("cancelProductForm").addEventListener("click", () => form.classList.add("hidden"));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("productId").value;
    const payload = {
      category_id: parseInt(document.getElementById("p_category").value),
      title: document.getElementById("p_title").value,
      description: document.getElementById("p_description").value,
      sunsky_sku: document.getElementById("p_sku").value,
      source_url: document.getElementById("p_url").value,
      cost: parseFloat(document.getElementById("p_cost").value) || 0,
      weight_g: parseFloat(document.getElementById("p_weight").value) || 0,
      warehouse_location: document.getElementById("p_warehouse").value,
      est_ship_days: parseInt(document.getElementById("p_ship_days").value) || 0,
      images: document
        .getElementById("p_images")
        .value.split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      status: document.getElementById("p_status").value,
      notes: "",
    };
    if (id) {
      await api(`/api/products/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } else {
      await api("/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }
    form.classList.add("hidden");
    await loadProducts();
    renderProductsTable();
  });
}

function resetProductForm() {
  document.getElementById("productId").value = "";
  ["p_title", "p_sku", "p_url", "p_images", "p_description"].forEach((id) => (document.getElementById(id).value = ""));
  document.getElementById("p_cost").value = "";
  document.getElementById("p_weight").value = "";
  document.getElementById("p_ship_days").value = "";
  document.getElementById("p_warehouse").value = "US";
  document.getElementById("p_status").value = "researching";
}

function setupCsvImport() {
  document.getElementById("csvImportBtn").addEventListener("click", async () => {
    const fileInput = document.getElementById("csv_file");
    const categoryId = document.getElementById("csv_category").value;
    const resultEl = document.getElementById("csvResult");
    if (!fileInput.files.length) {
      resultEl.textContent = "Choose a CSV file first.";
      return;
    }
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    resultEl.textContent = "Importing...";
    try {
      const res = await fetch(`/api/products/import-csv?category_id=${categoryId}`, { method: "POST", body: fd });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Import failed");
      resultEl.textContent = `Imported ${json.created} products.` + (json.warnings.length ? " Warnings: " + json.warnings.join("; ") : "");
      await loadProducts();
      renderProductsTable();
    } catch (err) {
      resultEl.textContent = "Error: " + err.message;
    }
  });
}

// ---------- Comps ----------
async function selectProduct(productId) {
  state.selectedProductId = productId;
  const product = state.products.find((p) => p.id === productId);
  document.getElementById("compsProductLabel").textContent = product ? `— ${product.title}` : "";
  await loadComps();
}

async function loadComps() {
  if (!state.selectedProductId) return;
  const comps = await api(`/api/products/${state.selectedProductId}/comps`);
  const container = document.getElementById("compsHistory");
  if (!comps.length) {
    container.innerHTML = '<p class="hint">No comps logged yet for this product.</p>';
    return;
  }
  container.innerHTML = `
    <table>
      <thead><tr><th>Marketplace</th><th>Price</th><th>Title</th><th>Source</th><th>Captured</th><th></th></tr></thead>
      <tbody>
        ${comps
          .map(
            (c) => `<tr>
              <td>${c.marketplace}</td><td>${money(c.price)}</td><td>${c.title || "-"}</td>
              <td>${c.source}</td><td>${new Date(c.captured_at).toLocaleDateString()}</td>
              <td><button class="btn-danger del-comp" data-id="${c.id}" type="button">Delete</button></td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>`;
  container.querySelectorAll(".del-comp").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/products/${state.selectedProductId}/comps/${btn.dataset.id}`, { method: "DELETE" });
      await loadComps();
    });
  });
}

function setupCompForm() {
  document.getElementById("compForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.selectedProductId) {
      alert("Click a product in the Margin Calculator table first.");
      return;
    }
    const payload = {
      marketplace: document.getElementById("comp_marketplace").value,
      price: parseFloat(document.getElementById("comp_price").value) || 0,
      title: document.getElementById("comp_title").value,
      url: document.getElementById("comp_url").value,
      source: "manual",
    };
    await api(`/api/products/${state.selectedProductId}/comps`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    document.getElementById("comp_price").value = "";
    document.getElementById("comp_title").value = "";
    document.getElementById("comp_url").value = "";
    await loadComps();
  });
}

// ---------- Listings ----------
function refreshListingProductOptions() {
  const sel = document.getElementById("listingProductSelect");
  const current = sel.value;
  sel.innerHTML = state.products.map((p) => `<option value="${p.id}">${p.title}</option>`).join("");
  if (current) sel.value = current;
  else if (state.selectedProductId) sel.value = state.selectedProductId;
  loadDrafts();
}

async function loadDrafts() {
  const productId = document.getElementById("listingProductSelect").value;
  const container = document.getElementById("draftsContainer");
  if (!productId) {
    container.innerHTML = "";
    return;
  }
  const drafts = await api(`/api/products/${productId}/drafts`);
  container.innerHTML = drafts.map(draftCardHtml).join("") || '<p class="hint">No drafts yet — generate one above.</p>';
  wireDraftCards();
}

function draftCardHtml(d) {
  return `
  <div class="draft-card" data-id="${d.id}">
    <div class="card-header"><h3>${d.marketplace}</h3>
      <div class="form-actions">
        <button class="btn-ghost copy-draft" type="button">Copy</button>
        <button class="btn-primary save-draft" type="button">Save edits</button>
        <button class="btn-danger del-draft" type="button">Delete</button>
      </div>
    </div>
    <input type="text" class="draft-title" value="${(d.title || "").replace(/"/g, "&quot;")}">
    <textarea class="draft-body">${d.body || ""}</textarea>
    <label class="hint">Tags (comma-separated)
      <input type="text" class="draft-tags" value="${(d.tags || []).join(", ")}">
    </label>
    <label class="hint">Price
      <input type="number" step="0.01" class="draft-price" value="${d.price}" style="width:100px">
    </label>
  </div>`;
}

function wireDraftCards() {
  document.querySelectorAll(".draft-card").forEach((card) => {
    const id = card.dataset.id;
    const productId = document.getElementById("listingProductSelect").value;

    card.querySelector(".copy-draft").addEventListener("click", () => {
      const title = card.querySelector(".draft-title").value;
      const body = card.querySelector(".draft-body").value;
      const tags = card.querySelector(".draft-tags").value;
      const text = `${title}\n\n${body}${tags ? "\n\nTags: " + tags : ""}`;
      navigator.clipboard.writeText(text).then(() => alert("Copied to clipboard."));
    });

    card.querySelector(".save-draft").addEventListener("click", async () => {
      const payload = {
        marketplace: card.querySelector("h3").textContent,
        title: card.querySelector(".draft-title").value,
        body: card.querySelector(".draft-body").value,
        tags: card
          .querySelector(".draft-tags")
          .value.split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        price: parseFloat(card.querySelector(".draft-price").value) || 0,
      };
      await api(`/api/products/${productId}/drafts/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      alert("Saved.");
    });

    card.querySelector(".del-draft").addEventListener("click", async () => {
      await api(`/api/products/${productId}/drafts/${id}`, { method: "DELETE" });
      loadDrafts();
    });
  });
}

function setupListingsTab() {
  document.getElementById("listingProductSelect").addEventListener("change", loadDrafts);
  document.querySelectorAll("[data-gen]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const productId = document.getElementById("listingProductSelect").value;
      if (!productId) {
        alert("Add a product first.");
        return;
      }
      await api(`/api/products/${productId}/drafts/generate/${btn.dataset.gen}`, { method: "POST" });
      loadDrafts();
    });
  });
}

// ---------- Orders ----------
async function refreshOrderProductOptions() {
  const sel = document.getElementById("o_product");
  sel.innerHTML = state.products.map((p) => `<option value="${p.id}">${p.title}</option>`).join("");
}

async function loadOrders() {
  await refreshOrderProductOptions();
  const orders = await api("/api/orders");
  const tbody = document.getElementById("ordersTableBody");
  tbody.innerHTML = orders
    .map(
      (o) => `
    <tr class="clickable" data-order-id="${o.id}">
      <td>${o.marketplace}</td>
      <td>${o.marketplace_order_id || "-"}</td>
      <td>${o.product_title}</td>
      <td>${money(o.sale_price)}</td>
      <td>${new Date(o.order_date).toLocaleDateString()}</td>
      <td>
        <select class="status-select" data-id="${o.id}">
          ${["needs_sourcing", "ordered_on_sunsky", "shipped", "delivered"]
            .map((s) => `<option value="${s}" ${s === o.status ? "selected" : ""}>${s.replace(/_/g, " ")}</option>`)
            .join("")}
        </select>
      </td>
      <td>${o.sunsky_order_id || "-"}</td>
      <td>${o.return_status}</td>
      <td><button class="btn-danger del-order" data-id="${o.id}" type="button">Delete</button></td>
    </tr>`
    )
    .join("");

  tbody.querySelectorAll(".status-select").forEach((sel) => {
    sel.addEventListener("click", (e) => e.stopPropagation());
    sel.addEventListener("change", async (e) => {
      e.stopPropagation();
      const order = orders.find((o) => o.id == sel.dataset.id);
      await api(`/api/orders/${sel.dataset.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...orderToPayload(order), status: sel.value }),
      });
    });
  });

  tbody.querySelectorAll(".del-order").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm("Delete this order?")) return;
      await api(`/api/orders/${btn.dataset.id}`, { method: "DELETE" });
      loadOrders();
    });
  });

  tbody.querySelectorAll("tr[data-order-id]").forEach((row) => {
    row.addEventListener("click", () => selectOrderForReturn(parseInt(row.dataset.orderId), orders));
  });
}

function orderToPayload(o) {
  return {
    marketplace: o.marketplace,
    marketplace_order_id: o.marketplace_order_id,
    product_id: o.product_id,
    sale_price: o.sale_price,
    sunsky_order_id: o.sunsky_order_id,
    status: o.status,
    tracking_number: o.tracking_number,
    notes: o.notes,
  };
}

async function selectOrderForReturn(orderId, orders) {
  const order = orders.find((o) => o.id === orderId);
  document.getElementById("returnPanel").style.display = "block";
  document.getElementById("returnOrderLabel").textContent = `— ${order.marketplace} / ${order.product_title}`;
  document.getElementById("r_order_id").value = orderId;
  const ret = await api(`/api/orders/${orderId}/return`);
  document.getElementById("r_status").value = ret ? ret.status : "none";
  document.getElementById("r_refund_amount").value = ret ? ret.refund_amount : 0;
  document.getElementById("r_reason").value = ret ? ret.reason : "";
  document.getElementById("r_notes").value = ret ? ret.notes : "";
}

function setupOrderForm() {
  const form = document.getElementById("orderForm");
  document.getElementById("toggleAddOrder").addEventListener("click", () => {
    form.classList.toggle("hidden");
  });
  document.getElementById("cancelOrderForm").addEventListener("click", () => form.classList.add("hidden"));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      marketplace: document.getElementById("o_marketplace").value,
      marketplace_order_id: document.getElementById("o_marketplace_order_id").value,
      product_id: parseInt(document.getElementById("o_product").value),
      sale_price: parseFloat(document.getElementById("o_sale_price").value) || 0,
      sunsky_order_id: document.getElementById("o_sunsky_order_id").value,
      status: document.getElementById("o_status").value,
      tracking_number: document.getElementById("o_tracking").value,
      notes: document.getElementById("o_notes").value,
    };
    await api("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    form.reset();
    form.classList.add("hidden");
    loadOrders();
  });

  document.getElementById("returnForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const orderId = document.getElementById("r_order_id").value;
    const payload = {
      status: document.getElementById("r_status").value,
      refund_amount: parseFloat(document.getElementById("r_refund_amount").value) || 0,
      reason: document.getElementById("r_reason").value,
      notes: document.getElementById("r_notes").value,
    };
    await api(`/api/orders/${orderId}/return`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    alert("Return record saved.");
    loadOrders();
  });
}

// ---------- Summary ----------
async function loadSummary() {
  const groupBy = document.getElementById("summaryGroupBy").value;
  const marketplace = document.getElementById("summaryMarketplace").value;
  const params = new URLSearchParams({ group_by: groupBy });
  if (marketplace) params.set("marketplace", marketplace);
  const rows = await api(`/api/summary?${params}`);
  document.getElementById("summaryTableBody").innerHTML = rows
    .map(
      (r) => `<tr>
        <td>${r.period}</td><td>${r.marketplace}</td><td>${money(r.revenue)}</td>
        <td>${money(r.cost)}</td><td>${money(r.refunds)}</td>
        <td class="${r.net_profit < 0 ? "flag-low" : ""}">${money(r.net_profit)}</td>
        <td>${r.order_count}</td>
      </tr>`
    )
    .join("");
}

function setupSummaryTab() {
  document.getElementById("summaryGroupBy").addEventListener("change", loadSummary);
  document.getElementById("summaryMarketplace").addEventListener("change", loadSummary);
}

// ---------- Init ----------
async function init() {
  setupTabs();
  setupSettingsModal();
  setupProductForm();
  setupCsvImport();
  setupCompForm();
  setupListingsTab();
  setupOrderForm();
  setupSummaryTab();

  document.getElementById("marginThreshold").addEventListener("change", async () => {
    await loadProducts();
    renderProductsTable();
  });

  await loadCategories();
  await loadFeeConfigs();
  await loadIntegrationStatus();
  await loadProducts();
  renderProductsTable();
}

document.addEventListener("DOMContentLoaded", init);
