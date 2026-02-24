'use client'

import { useState } from 'react'
import SearchBar from '@/components/SearchBar'
import ProductCard, { Product } from '@/components/ProductCard'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setQuery(searchQuery)
    setLoading(true)
    setError('')
    setSearched(true)

    try {
      const res = await fetch(
        `${API_URL}/search?q=${encodeURIComponent(searchQuery)}`
      )
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setProducts(data.results ?? [])
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

        {/* Error */}
        {!loading && error && (
          <div className="text-center py-16">
            <p className="text-2xl mb-2">⚠️</p>
            <p className="text-red-500 font-medium">{error}</p>
          </div>
        )}

        {/* Empty state after search */}
        {!loading && !error && searched && products.length === 0 && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">🔍</p>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">No products found</h2>
            <p className="text-gray-500">
              Try searching for an influencer name, brand, or category like &quot;skincare&quot; or &quot;makeup&quot;
            </p>
          </div>
        )}

        {/* Default landing state */}
        {!loading && !searched && (
          <div className="text-center py-20">
            <p className="text-6xl mb-6">✨</p>
            <h2 className="text-2xl font-semibold text-gray-700 mb-3">
              Search for anything
            </h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Try &quot;Charlotte Tilbury&quot;, &quot;Sarah Hany skincare&quot;, or &quot;best foundation&quot;
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {['skincare', 'makeup', 'haircare', 'fragrance'].map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleSearch(tag)}
                  className="px-4 py-2 rounded-full bg-pink-100 text-pink-700 hover:bg-pink-200 transition-colors capitalize font-medium text-sm"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results grid */}
        {!loading && !error && products.length > 0 && (
          <>
            <p className="text-gray-500 mb-6 font-medium">
              Found {products.length} product{products.length !== 1 ? 's' : ''} for &quot;{query}&quot;
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
