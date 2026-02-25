'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Product = {
  id: string;
  influencer_name: string;
  influencer_profile_pic?: string;
  product_name: string;
  brand: string;
  category: string;
  quote: string;
  video_url: string;
  platform: string;
  buy_links: Array<{
    id: string;
    store_name: string;
    url: string;
    price?: string;
    currency?: string;
  }>;
};

export default function ManageProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedInfluencer, setSelectedInfluencer] = useState('all');
  const [influencers, setInfluencers] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Product | null>(null);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/products?limit=1000`);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      
      const data = await res.json();
      const productsList = data.results || [];
      setProducts(productsList);
      
      if (productsList.length > 0) {
        const uniqueInfluencers = [...new Set(productsList.map((p: Product) => p.influencer_name))];
        setInfluencers(uniqueInfluencers);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
      alert(`Failed to load products: ${err}`);
    } finally {
      setLoading(false);
    }
  };

const startEdit = (product: Product) => {
  setEditingId(product.id);
  
  // ✅ DEEP COPY with buy_links properly cloned
  const productCopy = {
    ...product,
    buy_links: product.buy_links.map(link => ({ ...link }))  // Clone each link
  };
  
  console.log('🔧 Starting edit:', productCopy);  // Debug log
  setEditData(productCopy);
};

  const cancelEdit = () => {
    setEditingId(null);
    setEditData(null);
  };

  const saveEdit = async () => {
    if (!editData) return;

    try {
      const res = await fetch(`${API_URL}/admin/update-product/${editData.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editData),
      });

      if (res.ok) {
        alert('✅ Product updated!');
        setEditingId(null);
        setEditData(null);
        loadProducts();
      } else {
        alert('❌ Failed to update product');
      }
    } catch (err) {
      alert('❌ Error updating product');
    }
  };

 const deleteProduct = async (productId: string, productName: string) => {
  if (!confirm(`Are you sure you want to delete "${productName}"?`)) return;

  try {
    const res = await fetch(`${API_URL}/admin/delete-product/${productId}`, {
      method: 'DELETE',
    });

    if (res.ok) {
      alert('✅ Product deleted!');
      
      // ✅ Remove from state instead of reloading
      setProducts(products.filter(p => p.id !== productId));
      
      // Update influencers list
      const remaining = products.filter(p => p.id !== productId);
      if (remaining.length > 0) {
        const uniqueInfluencers = [...new Set(remaining.map(p => p.influencer_name))];
        setInfluencers(uniqueInfluencers);
      } else {
        setInfluencers([]);
      }
    } else {
      alert('❌ Failed to delete product');
    }
  } catch (err) {
    console.error('Delete error:', err);
    alert('❌ Error deleting product');
  }
};

  const updateEditField = (field: string, value: any) => {
    if (!editData) return;
    setEditData({ ...editData, [field]: value });
  };

  const updateBuyLink = (index: number, field: string, value: string) => {
  if (!editData) return;
  const newLinks = [...editData.buy_links];
  newLinks[index] = { ...newLinks[index], [field]: value };
  
  console.log(`📝 Updated link ${index}:`, newLinks[index]);  // Debug
  setEditData({ ...editData, buy_links: newLinks });
};

  const addBuyLink = () => {
    if (!editData) return;
    setEditData({
      ...editData,
      buy_links: [...editData.buy_links, { id: '', store_name: '', url: '', currency: 'EGP' }]
    });
  };

  const removeBuyLink = (index: number) => {
    if (!editData) return;
    const newLinks = editData.buy_links.filter((_, i) => i !== index);
    setEditData({ ...editData, buy_links: newLinks });
  };

  const filteredProducts = products.filter(p => {
    const matchesSearch = 
      p.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.influencer_name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesInfluencer = selectedInfluencer === 'all' || p.influencer_name === selectedInfluencer;

    return matchesSearch && matchesInfluencer;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              📦 Manage Products
            </h1>
            <a href="/admin" className="text-purple-600 hover:text-purple-800">
              ← Back to Admin
            </a>
          </div>
          <a 
            href="/admin"
            className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition"
          >
            + Add New Influencer
          </a>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Search Products</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by product, brand, or influencer..."
                className="w-full px-4 py-3 border rounded-lg text-black"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Filter by Influencer</label>
              <select
                value={selectedInfluencer}
                onChange={(e) => setSelectedInfluencer(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg text-black"
              >
                <option value="all">All Influencers ({products.length})</option>
                {influencers.map(inf => (
                  <option key={inf} value={inf}>
                    {inf} ({products.filter(p => p.influencer_name === inf).length})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="spinner w-12 h-12 rounded-full border-4 border-purple-200 border-t-purple-500 mb-4 mx-auto" />
            <p className="text-lg font-medium text-purple-500">Loading products...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-gray-600 font-medium">
              Showing {filteredProducts.length} of {products.length} products
            </p>

            {filteredProducts.map((product) => {
              const isEditing = editingId === product.id;
              const displayProduct = isEditing && editData ? editData : product;

              return (
                <div key={product.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
                  <div className="flex gap-4">
                    {/* Profile Pic */}
                    <div className="flex-shrink-0">
                      {product.influencer_profile_pic ? (
                        <img
                          src={`${API_URL}/api/proxy-image?url=${encodeURIComponent(product.influencer_profile_pic)}`}
                          alt={product.influencer_name}
                          className="w-16 h-16 rounded-full border-2 border-purple-300 object-cover"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            e.currentTarget.nextElementSibling?.classList.remove('hidden');
                          }}
                        />
                      ) : null}
                      <div className={`w-16 h-16 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white font-bold text-xl ${product.influencer_profile_pic ? 'hidden' : ''}`}>
                        {product.influencer_name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                    </div>

                    {/* Product Info */}
                    <div className="flex-1">
                      {isEditing ? (
                        /* EDIT MODE */
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium mb-1">Product Name</label>
                              <input
                                type="text"
                                value={displayProduct.product_name}
                                onChange={(e) => updateEditField('product_name', e.target.value)}
                                className="w-full px-3 py-2 border rounded text-black"
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-1">Brand</label>
                              <input
                                type="text"
                                value={displayProduct.brand}
                                onChange={(e) => updateEditField('brand', e.target.value)}
                                className="w-full px-3 py-2 border rounded text-black"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">Category</label>
                            <select
                              value={displayProduct.category}
                              onChange={(e) => updateEditField('category', e.target.value)}
                              className="w-full px-3 py-2 border rounded text-black"
                            >
                              <option value="makeup">Makeup</option>
                              <option value="skincare">Skincare</option>
                              <option value="haircare">Haircare</option>
                              <option value="fragrance">Fragrance</option>
                              <option value="fashion">Fashion</option>
                              <option value="shoes">Shoes</option>
                              <option value="bags">Bags & Accessories</option>
                              <option value="jewelry">Jewelry</option>
                              <option value="tech">Tech & Gadgets</option>
                              <option value="food">Food & Drinks</option>
                              <option value="lifestyle">Lifestyle</option>
                              <option value="home">Home Decor</option>
                              <option value="other">Other</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium mb-1">Quote</label>
                            <textarea
                              value={displayProduct.quote}
                              onChange={(e) => updateEditField('quote', e.target.value)}
                              className="w-full px-3 py-2 border rounded text-black"
                              rows={2}
                            />
                          </div>

                          <div>
                            <div className="flex justify-between items-center mb-2">
                              <label className="block text-sm font-medium">Buy Links</label>
                              <button
                                onClick={addBuyLink}
                                className="text-sm text-purple-600 hover:text-purple-800 font-bold"
                              >
                                + Add Link
                              </button>
                            </div>
                            {displayProduct.buy_links.map((link, idx) => (
                              <div key={idx} className="flex gap-2 mb-2">
                                <input
                                  type="text"
                                  value={link.store_name}
                                  onChange={(e) => updateBuyLink(idx, 'store_name', e.target.value)}
                                  placeholder="Store name"
                                  className="w-40 px-3 py-2 border rounded text-sm text-black"
                                />
                                <input
                                  type="url"
                                  value={link.url}
                                  onChange={(e) => updateBuyLink(idx, 'url', e.target.value)}
                                  placeholder="URL"
                                  className="flex-1 px-3 py-2 border rounded text-sm text-black"
                                />
                                <button
                                  onClick={() => removeBuyLink(idx)}
                                  className="px-3 py-2 bg-red-100 text-red-600 rounded hover:bg-red-200 text-sm font-bold"
                                >
                                  ✕
                                </button>
                              </div>
                            ))}
                          </div>

                          <div className="flex gap-2 pt-4 border-t">
                            <button
                              onClick={saveEdit}
                              className="px-6 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700"
                            >
                              💾 Save
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="px-6 py-2 bg-gray-300 text-gray-800 rounded-lg font-bold hover:bg-gray-400"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        /* VIEW MODE */
                        <>
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h3 className="text-xl font-bold text-gray-900">{product.product_name}</h3>
                              <p className="text-sm text-purple-600 font-medium">{product.brand}</p>
                              <p className="text-sm text-gray-500">By: {product.influencer_name}</p>
                            </div>
                            <div className="flex gap-2">
                              <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">
                                {product.category}
                              </span>
                              <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-semibold">
                                {product.platform}
                              </span>
                            </div>
                          </div>

                          {product.quote && (
                            <blockquote className="text-sm text-gray-600 italic border-l-4 border-pink-300 pl-3 mb-3">
                              "{product.quote}"
                            </blockquote>
                          )}

                          <div className="mb-3">
                            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Buy Links:</p>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                              {product.buy_links.map((link, idx) => (
                                <a
                                  key={idx}
                                  href={link.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs bg-gray-50 hover:bg-gray-100 px-3 py-2 rounded border truncate"
                                >
                                  {link.store_name}
                                </a>
                              ))}
                            </div>
                          </div>

                          <div className="flex gap-2">
                            {product.video_url && (
                              <a
                                href={product.video_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-purple-600 hover:text-purple-800 font-medium"
                              >
                                📹 Watch Video
                              </a>
                            )}
                            <button
                              onClick={() => startEdit(product)}
                              className="ml-auto text-sm text-blue-600 hover:text-blue-800 font-bold"
                            >
                              ✏️ Edit
                            </button>
                            <button
                              onClick={() => deleteProduct(product.id)}
                              className="text-sm text-red-600 hover:text-red-800 font-bold"
                            >
                              🗑️ Delete
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredProducts.length === 0 && (
              <div className="text-center py-20 text-gray-500">
                <p className="text-xl">No products found</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}