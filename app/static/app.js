/* ============================================================
   Artisan Coffee & Bakery — Mini App logic (Vanilla JS)
   Works both inside Telegram (MainButton, initData) and in a
   standalone desktop browser (mock user, demo mode).
   ============================================================ */

"use strict";

// ------------------------------------------------------------ Telegram bridge
const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const isTelegram = Boolean(tg && tg.initData !== undefined && tg.platform && tg.platform !== "unknown");
const isStandalone = !isTelegram;

const CATEGORY_TITLES = {
    all: "Всё",
    coffee: "Кофе",
    desserts: "Десерты",
    breakfast: "Завтраки",
};

// ------------------------------------------------------------ application state
let products = [];
let cart = {};        // { productId: quantity }
let activeCategory = "all";
let currentStep = "cart"; // cart | checkout | success
let lastOrderInfo = null;

// ------------------------------------------------------------ helpers
const $ = (id) => document.getElementById(id);

function formatPrice(value) {
    const rounded = Math.round(value);
    return `${rounded.toLocaleString("ru-RU")} ₽`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
}

function showToast(message) {
    const toast = $("toast");
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 2200);
}

function getCartEntries() {
    return Object.entries(cart)
        .map(([id, quantity]) => {
            const product = products.find((p) => p.id === Number(id));
            return product ? { product, quantity } : null;
        })
        .filter(Boolean);
}

function getCartTotal() {
    return getCartEntries().reduce((sum, { product, quantity }) => sum + product.price * quantity, 0);
}

function getCartCount() {
    return Object.values(cart).reduce((sum, q) => sum + q, 0);
}

// ------------------------------------------------------------ Telegram integration
function initTelegram() {
    if (!tg) return;

    tg.ready();

    if (tg.expand) tg.expand();
    if (tg.setHeaderColor) { try { tg.setHeaderColor("bg_color"); } catch (e) { /* optional API */ } }
    if (tg.setBackgroundColor) { try { tg.setBackgroundColor("secondary_bg_color"); } catch (e) { /* optional API */ } }

    // MainButton: "Оформить заказ • {сумма} ₽"
    tg.MainButton.setParams({
        text: mainButtonText(),
        is_visible: false,
        is_active: true,
    });
    tg.MainButton.onClick(onMainButtonClick);
}

function mainButtonText() {
    return `Оформить заказ • ${formatPrice(getCartTotal())}`;
}

function updateMainButton() {
    if (!tg) return;
    if (currentStep === "success") {
        tg.MainButton.hide();
        return;
    }
    if (getCartCount() > 0) {
        tg.MainButton.setParams({
            text: mainButtonText(),
            is_visible: true,
            is_active: true,
        });
    } else {
        tg.MainButton.hide();
    }
}

function onMainButtonClick() {
    if (getCartCount() === 0) {
        showToast("Сначала добавьте товары в корзину 🛒");
        return;
    }
    openCart();
}

// ------------------------------------------------------------ theme handling
function applyTheme() {
    if (!tg || !tg.colorScheme) return;
    // tg.colorScheme is "light" | "dark"; Telegram already injects the
    // --tg-theme-* variables. For standalone we use media-query fallback.
    if (isStandalone && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        document.body.classList.add("standalone-dark");
    }
}

// ------------------------------------------------------------ catalogue
async function loadProducts() {
    $("loading").classList.remove("hidden");
    $("error-state").classList.add("hidden");
    $("products-list").innerHTML = "";

    try {
        const response = await fetch("/api/products");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        products = await response.json();
        renderProducts();
    } catch (error) {
        console.error("Failed to load products:", error);
        $("error-state").classList.remove("hidden");
    } finally {
        $("loading").classList.add("hidden");
    }
}

function renderProducts() {
    const list = $("products-list");
    const filtered = activeCategory === "all"
        ? products
        : products.filter((p) => p.category === activeCategory);

    if (filtered.length === 0) {
        list.innerHTML = `
            <p class="text-center py-10 text-sm" style="color: var(--tg-theme-hint-color);">
                В этой категории пока нет товаров
            </p>`;
        return;
    }

    // Group products by category for section headings
    const groups = new Map();
    for (const product of filtered) {
        if (!groups.has(product.category)) groups.set(product.category, []);
        groups.get(product.category).push(product);
    }

    let html = "";
    for (const [category, items] of groups) {
        html += `
            <h2 class="font-bold text-sm uppercase tracking-wide mt-2" style="color: var(--tg-theme-hint-color);">
                ${CATEGORY_TITLES[category] || category}
            </h2>`;
        html += items.map(renderProductCard).join("");
    }
    list.innerHTML = html;
}

function renderProductCard(product) {
    const quantity = cart[product.id] || 0;
    return `
        <div class="product-card">
            <div class="product-emoji">${escapeHtml(product.image_url)}</div>
            <div class="flex-1 min-w-0 flex flex-col gap-1">
                <div class="flex items-start justify-between gap-2">
                    <h3 class="font-bold text-sm leading-snug">${escapeHtml(product.title)}</h3>
                    <span class="font-bold text-sm whitespace-nowrap">${formatPrice(product.price)}</span>
                </div>
                <p class="text-xs leading-relaxed line-clamp-2" style="color: var(--tg-theme-hint-color);">
                    ${escapeHtml(product.description)}
                </p>
                <div class="flex items-center justify-between mt-auto pt-1">
                    <div class="flex items-center gap-2 ${quantity === 0 ? "invisible" : ""}" id="stepper-${product.id}">
                        <button class="qty-btn minus" onclick="changeQuantity(${product.id}, -1)" aria-label="Убрать одну штуку">−</button>
                        <span class="qty-value">${quantity}</span>
                        <button class="qty-btn" onclick="changeQuantity(${product.id}, 1)" aria-label="Добавить одну штуку">+</button>
                    </div>
                    ${quantity === 0
                        ? `<button class="qty-btn" style="width:2.1rem;" onclick="changeQuantity(${product.id}, 1)" aria-label="Добавить в корзину">+</button>`
                        : ""}
                </div>
            </div>
        </div>`;
}

// ------------------------------------------------------------ cart mutations
function changeQuantity(productId, delta) {
    const current = cart[productId] || 0;
    const next = Math.max(0, Math.min(99, current + delta));

    if (next === 0) delete cart[productId];
    else cart[productId] = next;

    renderProducts();
    updateCartUi();
}

function updateCartUi() {
    const count = getCartCount();
    const total = getCartTotal();

    // Header pill
    const previewBtn = $("cart-preview-btn");
    if (count > 0) {
        previewBtn.classList.remove("hidden");
        previewBtn.classList.add("flex");
        $("cart-preview-count").textContent = count;
    } else {
        previewBtn.classList.add("hidden");
        previewBtn.classList.remove("flex");
    }

    // Floating cart button (hidden when modal is open)
    const fab = $("cart-fab");
    if (count > 0 && $("modal-overlay").classList.contains("hidden")) {
        fab.classList.remove("hidden");
        $("fab-total").textContent = formatPrice(total);
    } else {
        fab.classList.add("hidden");
    }

    updateMainButton();

    // Re-render cart modal contents if the cart step is visible
    if (currentStep === "cart" && !$("modal-overlay").classList.contains("hidden")) {
        renderCartItems();
    }
}

// ------------------------------------------------------------ modal / checkout
function openCart() {
    currentStep = "cart";
    showStep("cart");
    $("modal-title").textContent = "🛒 Корзина";
    $("modal-action-btn").textContent = "Оформить заказ";
    $("cart-fab").classList.add("hidden");
    $("modal-overlay").classList.remove("hidden");
    if (tg && tg.disableVerticalSwipes) { try { tg.disableVerticalSwipes(); } catch (e) { /* optional */ } }
    renderCartItems();
    updateModalActionButton();
}

function closeCart() {
    $("modal-overlay").classList.add("hidden");
    if (currentStep === "success") resetAfterSuccess();
    updateCartUi();
}

function renderCartItems() {
    const container = $("cart-items");
    const entries = getCartEntries();

    if (entries.length === 0) {
        container.innerHTML = "";
        $("cart-empty").classList.remove("hidden");
        updateModalActionButton();
        return;
    }
    $("cart-empty").classList.add("hidden");
    container.innerHTML = entries.map(({ product, quantity }) => `
        <div class="flex items-center gap-3 tg-secondary p-3 rounded-2xl">
            <div class="product-emoji" style="width:3rem;height:3rem;min-width:3rem;font-size:1.5rem;">
                ${escapeHtml(product.image_url)}
            </div>
            <div class="flex-1 min-w-0">
                <p class="font-semibold text-sm truncate">${escapeHtml(product.title)}</p>
                <p class="text-xs" style="color: var(--tg-theme-hint-color);">
                    ${formatPrice(product.price)} × ${quantity} = ${formatPrice(product.price * quantity)}
                </p>
            </div>
            <div class="flex items-center gap-2">
                <button class="qty-btn minus" onclick="changeQuantity(${product.id}, -1)">−</button>
                <span class="qty-value">${quantity}</span>
                <button class="qty-btn" onclick="changeQuantity(${product.id}, 1)">+</button>
            </div>
        </div>
    `).join("");
    updateModalActionButton();
}

function updateModalActionButton() {
    const btn = $("modal-action-btn");
    const entries = getCartEntries();
    if (currentStep === "cart") {
        btn.textContent = entries.length === 0 ? "Корзина пуста" : `Оформить заказ • ${formatPrice(getCartTotal())}`;
        btn.disabled = entries.length === 0;
    } else if (currentStep === "checkout") {
        btn.textContent = `Подтвердить заказ • ${formatPrice(getCartTotal())}`;
        btn.disabled = false;
    } else if (currentStep === "success") {
        btn.textContent = "Отлично, спасибо!";
        btn.disabled = false;
    }
}

function onModalAction() {
    if (currentStep === "cart") {
        if (getCartCount() === 0) return;
        currentStep = "checkout";
        showStep("checkout");
        $("modal-title").textContent = "📦 Оформление заказа";
        $("cart-items").innerHTML = "";
        $("cart-empty").classList.add("hidden");
        renderCheckoutSummary();
        updateModalActionButton();
    } else if (currentStep === "checkout") {
        submitOrder();
    } else if (currentStep === "success") {
        closeCart();
    }
}

function renderCheckoutSummary() {
    const entries = getCartEntries();
    const rows = entries.map(({ product, quantity }) => `
        <div class="flex justify-between gap-3">
            <span class="truncate">${escapeHtml(product.title)} × ${quantity}</span>
            <span class="whitespace-nowrap font-medium">${formatPrice(product.price * quantity)}</span>
        </div>`).join("");
    $("checkout-summary").innerHTML = `
        ${rows}
        <div class="flex justify-between gap-3 pt-2 mt-2 border-t font-bold"
             style="border-color: var(--tg-theme-hint-color);">
            <span>Итого</span>
            <span>${formatPrice(getCartTotal())}</span>
        </div>`;
}

async function submitOrder() {
    const address = $("input-address").value.trim();
    const comment = $("input-comment").value.trim();
    const guestName = $("input-name").value.trim();
    const phone = $("input-phone").value.trim();

    const errorEl = $("checkout-error");
    errorEl.classList.add("hidden");

    if (!address) {
        errorEl.textContent = "Укажите адрес доставки или номер столика.";
        errorEl.classList.remove("hidden");
        return;
    }

    const btn = $("modal-action-btn");
    btn.disabled = true;
    btn.textContent = "Отправляем…";

    const payload = {
        items: getCartEntries().map(({ product, quantity }) => ({
            product_id: product.id,
            title: product.title,
            price: product.price,
            quantity,
        })),
        address,
        comment,
        guest_name: isTelegram ? "" : guestName,
    };

    const headers = { "Content-Type": "application/json" };
    if (isTelegram && tg.initData) {
        headers["X-Init-Data"] = tg.initData;
    }

    try {
        const response = await fetch("/api/order", {
            method: "POST",
            headers,
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`);
        }
        lastOrderInfo = {
            orderId: data.order_id,
            total: data.total_price,
            address,
            phone,
            adminNotified: data.admin_notified,
            entries: getCartEntries(),
        };
        showSuccess();
    } catch (error) {
        console.error("Order failed:", error);
        errorEl.textContent = `Не удалось отправить заказ: ${error.message}`;
        errorEl.classList.remove("hidden");
        updateModalActionButton();
    }
}

function showSuccess() {
    currentStep = "success";
    showStep("success");
    $("modal-title").textContent = "✅ Заказ принят";
    $("success-order-id").textContent = `№${lastOrderInfo.orderId}`;
    $("success-details").innerHTML = `
        <div class="flex flex-col gap-1.5">
            ${lastOrderInfo.entries.map(({ product, quantity }) => `
                <div class="flex justify-between">
                    <span>${escapeHtml(product.title)} × ${quantity}</span>
                    <span>${formatPrice(product.price * quantity)}</span>
                </div>`).join("")}
            <div class="flex justify-between font-bold pt-2 mt-1 border-t" style="border-color: var(--tg-theme-hint-color);">
                <span>Итого</span><span>${formatPrice(lastOrderInfo.total)}</span>
            </div>
            <p class="pt-2" style="color: var(--tg-theme-hint-color);">📍 ${escapeHtml(lastOrderInfo.address)}</p>
            ${lastOrderInfo.adminNotified
                ? "<p style='color: var(--tg-theme-hint-color);'>📨 Менеджер уже получил уведомление.</p>"
                : "<p style='color: var(--tg-theme-hint-color);'>ℹ️ Демо-режим: уведомление менеджеру отключено.</p>"}
        </div>`;
    cart = {};
    renderProducts();
    updateModalActionButton();
    updateMainButton();
    if (tg && tg.HapticFeedback) {
        try { tg.HapticFeedback.notificationOccurred("success"); } catch (e) { /* optional API */ }
    }
}

function resetAfterSuccess() {
    currentStep = "cart";
    lastOrderInfo = null;
    $("input-address").value = "";
    $("input-phone").value = "";
    $("input-name").value = "";
    $("input-comment").value = "";
    $("checkout-error").classList.add("hidden");
}

function showStep(step) {
    $("step-cart").classList.toggle("hidden", step !== "cart");
    $("step-checkout").classList.toggle("hidden", step !== "checkout");
    $("step-success").classList.toggle("hidden", step !== "success");
}

// ------------------------------------------------------------ init
document.addEventListener("DOMContentLoaded", () => {
    initTelegram();
    applyTheme();

    if (isStandalone) {
        $("standalone-banner").classList.remove("hidden");
    }

    // Category tabs
    document.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            activeCategory = btn.dataset.category;
            renderProducts();
        });
    });

    // Preselect the "all" tab
    document.querySelector('.tab-btn[data-category="all"]').classList.add("active");

    // Listen for Telegram theme changes
    if (tg && tg.onEvent) {
        try {
            tg.onEvent("themeChanged", applyTheme);
        } catch (e) { /* optional API */ }
    }

    // Standalone dark-mode detection
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyTheme);
    }

    // Close modal on Escape (desktop convenience)
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !$("modal-overlay").classList.contains("hidden")) {
            closeCart();
        }
    });

    // Back button inside Telegram closes the modal
    if (tg && tg.BackButton) {
        try {
            tg.BackButton.onClick(() => {
                if (!$("modal-overlay").classList.contains("hidden")) closeCart();
            });
        } catch (e) { /* optional API */ }
    }

    loadProducts();
});