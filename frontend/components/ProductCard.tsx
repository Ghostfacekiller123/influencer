export interface BuyLink {
  id?: string
  store: string
  price?: number | null
  currency?: string
  url: string
  in_stock?: boolean
}

export interface Product {
  id?: string
  influencer_name: string
  product_name: string
  brand?: string
  category?: string
  quote?: string
  video_url?: string
  platform?: string
  buy_links?: BuyLink[]
}

const CATEGORY_COLORS: Record<string, string> = {
  skincare: 'bg-green-100 text-green-800',
  makeup: 'bg-pink-100 text-pink-800',
  haircare: 'bg-yellow-100 text-yellow-800',
  fragrance: 'bg-purple-100 text-purple-800',
  fashion: 'bg-blue-100 text-blue-800',
  food: 'bg-orange-100 text-orange-800',
  tech: 'bg-gray-100 text-gray-800',
  other: 'bg-slate-100 text-slate-700',
}

const STORE_ICONS: Record<string, string> = {
  'Amazon.eg': '🛒',
  'Noon Egypt': '🌙',
  'Jumia Egypt': '📦',
}

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const categoryClass =
    CATEGORY_COLORS[product.category?.toLowerCase() ?? 'other'] ??
    CATEGORY_COLORS['other']

  const platformIcon = product.platform === 'instagram' ? '📸' : '🎵'

  return (
    <div className="product-card bg-white rounded-2xl shadow-md p-5 flex flex-col gap-3 border border-gray-100">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-bold text-gray-900 leading-tight">
            {product.product_name}
          </h3>
          {product.brand && (
            <p className="text-sm text-purple-600 font-medium mt-0.5">{product.brand}</p>
          )}
        </div>
        {product.category && (
          <span className={`text-xs font-semibold px-2 py-1 rounded-full shrink-0 capitalize ${categoryClass}`}>
            {product.category}
          </span>
        )}
      </div>

      {/* Influencer */}
      <p className="text-sm text-gray-500">
        <span className="font-medium text-gray-700">By:</span> {product.influencer_name}
      </p>

      {/* Quote */}
      {product.quote && (
        <blockquote className="text-sm text-gray-600 italic border-l-4 border-pink-300 pl-3 line-clamp-3">
          &ldquo;{product.quote}&rdquo;
        </blockquote>
      )}

      {/* Video link */}
      {product.video_url && (
        <a
          href={product.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-sm text-purple-600 hover:text-purple-800 font-medium transition-colors"
        >
          {platformIcon} Watch video
        </a>
      )}

      {/* Buy links */}
      {product.buy_links && product.buy_links.length > 0 && (
        <div className="border-t border-gray-100 pt-3 mt-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Buy in Egypt
          </p>
          <div className="flex flex-col gap-2">
            {product.buy_links.map((link, i) => (
              <div key={link.id ?? i} className="flex items-center justify-between gap-2">
                <span className="text-sm text-gray-700 font-medium">
                  {STORE_ICONS[link.store] ?? '🛍️'} {link.store}
                </span>
                <div className="flex items-center gap-2">
                  {link.price && (
                    <span className="text-sm font-bold text-gray-900">
                      {link.price.toLocaleString()} {link.currency ?? 'EGP'}
                    </span>
                  )}
                  {link.in_stock === false ? (
                    <span className="text-xs text-red-500 font-medium">Out of stock</span>
                  ) : (
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all"
                    >
                      Buy
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
