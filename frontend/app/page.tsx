'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'
import SearchBar from '@/components/SearchBar'
import ProductCard, { Product } from '@/components/ProductCard'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState('')
  const [aiMode, setAiMode] = useState(true)
  const [aiAnswer, setAiAnswer] = useState('')



  const loadAllProducts = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('products')
      .select(`
        *,
        buy_links (*)
      `)
      .order('created_at', { ascending: false })

    if (!error && data) {
      setProducts(data as any)
    }
    setLoading(false)
  }

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setQuery(searchQuery)
    setLoading(true)
    setError('')
    setSearched(true)
    setAiAnswer('')

    try {
      if (aiMode) {
        // AI-powered Q&A
        const res = await fetch(`${API_URL}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: searchQuery })
        })
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        const data = await res.json()
        setAiAnswer(data.answer)
        setProducts(data.products ?? [])
      } else {
        // Regular search
        const res = await fetch(
          `${API_URL}/search?q=${encodeURIComponent(searchQuery)}`
        )
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        const data = await res.json()
        setProducts(data.results ?? [])
      }
    } catch (err) {
      setError('Failed to fetch results. Is the backend running?')
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-pink-500 via-purple-500 to-purple-700 text-white py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-4 drop-shadow-lg">
            What Does She Use? 💄
          </h1>
          <p className="text-lg md:text-xl text-pink-100 mb-10">
            Discover products used by top Egyptian & MENA influencers.
            Find where to buy in Egypt with the best prices.
          </p>
          <SearchBar onSearch={handleSearch} initialQuery={query} />
        </div>
      </section>

      {/* Results Section */}
      <section className="max-w-6xl mx-auto px-4 py-12">
        {/* Loading */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 text-purple-500">
            <div className="spinner w-12 h-12 rounded-full border-4 border-purple-200 border-t-purple-500 mb-4" />
            <p className="text-lg font-medium">Searching…</p>
          </div>
        )}

        {/* Error state */}
        {!loading && error && (
          <div className="text-center py-10">
            <p className="text-red-500">{error}</p>
          </div>
        )}

        {/* AI Answer */}
        {!loading && aiAnswer && (
          <div className="max-w-3xl mx-auto mb-8 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-2xl p-6">
            <div className="flex items-start gap-3">
              <span className="text-3xl">💡</span>
              <div>
                <h3 className="font-bold text-purple-900 mb-2">AI Answer:</h3>
                <p className="text-gray-700 leading-relaxed">{aiAnswer}</p>
              </div>
            </div>
          </div>
        )}

        {/* Empty state after search */}
        {!loading && searched && products.length === 0 && !error && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">🔍</p>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">No products found</h2>
            <p className="text-gray-500">
              Try searching for an influencer name, brand, or category like &quot;skincare&quot; or &quot;makeup&quot;
            </p>
          </div>
        )}

        {/* Results grid */}
     {!loading && products.length > 0 && (
  <>
    <p className="text-gray-500 mb-6 font-medium">
      {aiAnswer
        ? `Found ${products.length} product${products.length !== 1 ? 's' : ''} used by ${products[0]?.influencer_name || 'this influencer'}`  // ✅ CHANGED
        : `Found ${products.length} product${products.length !== 1 ? 's' : ''} for "${query}"`
      }
    </p>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product, index) => (
                <div
                  key={product.id ?? index}
                  className="animate-fade-in-up"
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  <ProductCard product={product} />
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </main>
  )
}