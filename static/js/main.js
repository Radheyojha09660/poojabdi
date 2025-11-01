document.addEventListener('DOMContentLoaded', function(){
  function fetchProducts(){ fetch('/products.json').then(r=>r.json()).then(renderProducts).catch(()=>{}); }
  function renderProducts(products){
    const grid = document.getElementById('products-grid'); if(!grid) return;
    grid.innerHTML = '';
    products.forEach(p=>{
      const img = p.img || '/static/images/no-image.png';
      const div = document.createElement('div'); div.className='product';
      div.innerHTML = `<img src="${img}" onerror="this.src='/static/images/no-image.png'"><h4>${p.name_hi||p.name_en}</h4><div class="price">${p.price||''}</div><div style="margin-top:8px"><button class="btn primary add" data-id="${p.id}">कार्ट में जोड़ें</button></div>`;
      grid.appendChild(div);
    });
    document.querySelectorAll('.add').forEach(b=> b.addEventListener('click', function(){
      const id = Number(this.dataset.id);
      fetch('/api/cart', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:id, qty:1})}).then(()=>updateCartCount());
    }));
  }
  function updateCartCount(){ fetch('/api/cart').then(r=>r.json()).then(cart=>{ const c = Object.values(cart).reduce((s,v)=>s+v,0); const el=document.getElementById('cart-count'); if(el) el.innerText=c; }); }
  // admin: add product
  const prodForm = document.getElementById('product-form');
  if(prodForm){
    prodForm.addEventListener('submit', function(e){
      e.preventDefault();
      const fd = new FormData(prodForm);
      fetch('/admin/api/product', {method:'POST', body: fd}).then(r=>r.json()).then(res=>{ if(res.ok) location.reload(); });
    });
  }
  // delete/edit
  document.addEventListener('click', function(e){
    if(e.target && e.target.matches('.delete')){
      const id = e.target.dataset.id;
      if(!confirm('Delete product?')) return;
      fetch('/admin/api/product', {method:'DELETE', headers:{'Content-Type':'application/json'}, body: JSON.stringify({id:id})}).then(r=>r.json()).then(res=>{ if(res.ok) location.reload(); });
    }
    if(e.target && e.target.matches('.edit')){
      const id = e.target.dataset.id;
      const name_hi = prompt('Name (HI)'); if(name_hi===null) return;
      const name_en = prompt('Name (EN)'); if(name_en===null) return;
      const price = prompt('Price'); const price_num = prompt('Price numeric')||0; const img = prompt('Image URL')||'';
      const fd = new FormData(); fd.append('id', id); fd.append('name_hi', name_hi); fd.append('name_en', name_en); fd.append('price', price); fd.append('price_num', price_num); fd.append('img', img);
      fetch('/admin/api/product', {method:'PUT', body: fd}).then(r=>r.json()).then(res=>{ if(res.ok) location.reload(); });
    }
  });
  // site settings save
  const siteForm = document.getElementById('site-form');
  if(siteForm){ siteForm.addEventListener('submit', function(e){ e.preventDefault(); const fd=new FormData(siteForm); fetch('/admin/api/settings', {method:'POST', body: fd}).then(r=>r.json()).then(res=>{ if(res.ok) alert('Saved'); }); }); }
  // cart drawer
  const cartBtn = document.getElementById('cart-btn'), cartDrawer = document.getElementById('cart-drawer'), cartOverlay = document.getElementById('cart-overlay');
  if(cartBtn) cartBtn.addEventListener('click', ()=>{ if(cartDrawer) cartDrawer.classList.add('open'); if(cartOverlay) cartOverlay.classList.add('visible'); loadCartItems(); });
  if(cartOverlay) cartOverlay.addEventListener('click', ()=>{ if(cartDrawer) cartDrawer.classList.remove('open'); if(cartOverlay) cartOverlay.classList.remove('visible'); });
  function loadCartItems(){ fetch('/api/cart').then(r=>r.json()).then(cart=>{ const wrap=document.getElementById('cart-items'); if(!wrap) return; wrap.innerHTML=''; let subtotal=0; fetch('/products.json').then(r=>r.json()).then(products=>{ Object.entries(cart).forEach(([pid, qty])=>{ const prod = products.find(p=>String(p.id)===String(pid)); if(!prod) return; const price = Number(prod.price_num||0); subtotal += price*qty; const item=document.createElement('div'); item.className='cart-item'; item.innerHTML = `<div style="display:flex;gap:8px;align-items:center"><img src="${prod.img||'/static/images/no-image.png'}" style="width:64px;height:50px;object-fit:cover"><div><div style="font-weight:700">${prod.name_hi||prod.name_en}</div><div style="color:var(--muted)">${prod.price||''}</div></div></div><div style="margin-top:8px">Qty: ${qty}</div>`; wrap.appendChild(item); }); document.getElementById('cart-subtotal').innerText = '₹'+subtotal.toFixed(2); }); }); }
  // init
  fetchProducts(); updateCartCount();
});
