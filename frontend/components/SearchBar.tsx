'use client'

import { useState } from 'react'

interface SearchBarProps {
  onSearch: (query: string) => void
  initialQuery?: string
}

export default function SearchBar({ onSearch, initialQuery = '' }: SearchBarProps) {
  const [value, setValue] = useState(initialQuery)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(value)
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-2xl mx-auto rounded-2xl overflow-hidden shadow-2xl"
      role="search"
    >
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask anything... 'What does she use for eyes?' 💄"
        aria-label="Search products"
        className="flex-1 px-6 py-4 text-gray-800 text-lg outline-none bg-white placeholder-gray-400"
      />
      <button
        type="submit"
        className="bg-pink-600 hover:bg-pink-700 active:bg-pink-800 text-white px-8 py-4 font-semibold text-lg transition-colors"
        aria-label="Submit search"
      >
        Ask AI ✨
      </button>
    </form>
  )
}