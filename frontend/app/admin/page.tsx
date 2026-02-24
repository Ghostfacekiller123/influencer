'use client';

import { useState } from 'react';

type Product = {
  product_name: string;
  brand: string;
  category: string;
  quote: string;
  buy_links: Array<{
    store_name: string;
    url: string;
    currency: string;
  }>;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminPage() {
  const [handle, setHandle] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'input' | 'verify' | 'saving'>('input');
  
  const [influencerName, setInfluencerName] = useState('');
  const [profilePic, setProfilePic] = useState('');
  const [products, setProducts] = useState<Product[]>([]);

  const handleParse = async () => {
    if (!handle.trim()) {
      alert('Please enter an influencer handle');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/admin/parse-influencer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle, platform, limit }),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Failed to parse influencer');

      setInfluencerName(data.influencer_name);
      setProfilePic(data.profile_pic || '');
      setProducts(data.products);
      setStep('verify');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setStep('saving');

    try {
      const res = await fetch(`${API_URL}/admin/save-products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          influencer_name: influencerName,
          profile_pic: profilePic,
          platform: platform,
          products,
        }),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Failed to save products');

      alert(`✅ Saved ${data.saved_count}/${data.total_count} products!`);
      
      setStep('input');
      setHandle('');
      setProducts([]);
    } catch (err: any) {
      alert(err.message);
      setStep('verify');
    } finally {
      setLoading(false);
    }
  };

  const updateProduct = (index: number, field: string, value: any) => {
    const updated = [...products];
    updated[index] = { ...updated[index], [field]: value };
    setProducts(updated);
  };

  const updateBuyLink = (productIndex: number, linkIndex: number, url: string) => {
    const updated = [...products];
    updated[productIndex].buy_links[linkIndex].url = url;
    setProducts(updated);
  };

  const removeProduct = (index: number) => {
    setProducts(products.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-purple-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🔧 Admin Panel
          </h1>
          <a href="/" className="text-purple-600 hover:text-purple-800">
            ← Back to Home
          </a>
        </div>

        {step === 'input' && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Add New Influencer</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Influencer Handle
                </label>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  placeholder="e.g. sarahhanyofficial"
                  className="w-full px-4 py-3 border rounded-lg text-black"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Platform</label>
                <select
                  value={platform}
                  onChange={(e) => setPlatform(e.target.value)}
                  className="w-full px-4 py-3 border rounded-lg text-black"
                >
                  <option value="instagram">Instagram</option>
                  <option value="tiktok">TikTok</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Number of Videos
                </label>
                <input
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  className="w-full px-4 py-3 border rounded-lg text-black"
                  min="1"
                  max="50"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Recommended: 5-20 videos
                </p>
              </div>

              <button
                onClick={handleParse}
                disabled={loading}
                className="w-full bg-gradient-to-r from-pink-500 to-purple-600 text-white py-4 rounded-lg font-semibold disabled:opacity-50"
              >
                {loading ? '⏳ Parsing...' : '🔍 Parse & Extract Products'}
              </button>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">
                Verify Products - {influencerName}
              </h2>
              <button
                onClick={() => setStep('input')}
                className="text-gray-600 hover:text-gray-800"
              >
                ← Back
              </button>
            </div>

            <p className="text-gray-600 mb-6">
              Found {products.length} products. Edit and add buy links:
            </p>

            <div className="space-y-6 max-h-[600px] overflow-y-auto pr-4">
              {products.map((product, pIdx) => (
                <div key={pIdx} className="border-2 rounded-lg p-6 bg-gray-50">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-bold text-gray-800">
                      {pIdx + 1}. {product.product_name}
                    </h3>
                    <button
                      onClick={() => removeProduct(pIdx)}
                      className="text-red-500 hover:text-red-700 font-bold"
                    >
                      ✕
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Brand</label>
                      <input
                        type="text"
                        value={product.brand}
                        onChange={(e) => updateProduct(pIdx, 'brand', e.target.value)}
                        className="w-full px-3 py-2 border rounded text-black"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Category</label>
                      <select
                        value={product.category}
                        onChange={(e) => updateProduct(pIdx, 'category', e.target.value)}
                        className="w-full px-3 py-2 border rounded text-black"
                      >
                        <option value="makeup">Makeup</option>
                        <option value="skincare">Skincare</option>
                        <option value="haircare">Haircare</option>
                        <option value="fragrance">Fragrance</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">Quote</label>
                    <textarea
                      value={product.quote}
                      onChange={(e) => updateProduct(pIdx, 'quote', e.target.value)}
                      className="w-full px-3 py-2 border rounded text-black"
                      rows={2}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Buy Links (leave empty to auto-generate)
                    </label>
                    {product.buy_links.map((link, lIdx) => (
                      <div key={lIdx} className="flex gap-2 mb-2">
                        <span className="px-3 py-2 bg-purple-100 rounded font-medium min-w-[140px] text-sm">
                          {link.store_name}
                        </span>
                        <input
                          type="url"
                          value={link.url}
                          onChange={(e) => updateBuyLink(pIdx, lIdx, e.target.value)}
                          placeholder="Optional - paste product URL"
                          className="flex-1 px-3 py-2 border rounded text-sm text-black"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {products.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No products found
              </div>
            ) : (
              <button
                onClick={handleSave}
                disabled={loading}
                className="w-full mt-6 bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-lg font-semibold disabled:opacity-50"
              >
                {loading ? '💾 Saving...' : `💾 Save ${products.length} Products`}
              </button>
            )}
          </div>
        )}

        {step === 'saving' && (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">⏳</div>
            <h2 className="text-2xl font-bold">Saving products...</h2>
          </div>
        )}
      </div>
    </div>
  );
}