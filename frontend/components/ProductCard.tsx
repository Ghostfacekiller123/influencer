export interface BuyLink {
  id?: string
  store_name: string
  price?: string | null
  currency?: string | null
  url: string
  in_stock?: boolean
}

export interface Product {
  id?: string
  influencer_name: string
  influencer_profile_pic?: string  // ← ADD THIS
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
  'Amazon Egypt': '🛒',
  'Noon Egypt': '🌙',
  'Jumia Egypt': '📦',
  'Google Shopping': '🔍',
}

// Fallback function to get icon
const getStoreIcon = (storeName: string) => {
  return STORE_ICONS[storeName] || '🛍️';
};

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const categoryClass =
    CATEGORY_COLORS[product.category?.toLowerCase() ?? 'other'] ??
    CATEGORY_COLORS['other']

  const platformIcon = product.platform === 'instagram' ? '📸' : '🎵'

  return (
    <div className="product-card bg-white rounded-2xl shadow-md p-5 flex flex-col gap-3 border border-gray-100 hover:shadow-xl transition-shadow">
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

      {/* Influencer WITH PROFILE PIC */}
      <div className="flex items-center gap-2">
        {product.influencer_profile_pic ? (
          <img
            src={product.influencer_profile_pic}
            alt={product.influencer_name}
            className="w-8 h-8 rounded-full border-2 border-purple-300 object-cover"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white font-bold text-xs">
            {product.influencer_name?.charAt(0)?.toUpperCase() || '?'}
          </div>
        )}
        <p className="text-sm text-gray-500">
          <span className="font-medium text-gray-700">By:</span> {product.influencer_name}
        </p>
      </div>

      {/* Quote */}
      {product.quote && (
        <blockquote className="text-sm text-gray-600 italic border-l-4 border-pink-300 pl-3 line-clamp-3">
          &ldquo;{product.quote}&rdquo;
        </blockquote>
      )}

      {/* Video link */}
      {product.video_url && product.video_url.trim() !== '' && (
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
      {product.buy_links && product.buy_links.length > 0 && (() => {
        const mentionLinks = product.buy_links.filter(l => l.store_name?.startsWith('@'))
        const shopLinks = product.buy_links.filter(l => !l.store_name?.startsWith('@'))
        return (
          <div className="border-t border-gray-100 pt-3 mt-1 flex flex-col gap-3">
            {mentionLinks.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Brand Links:
                </p>
                <div className="flex flex-col gap-2">
                  {mentionLinks.map((link, i) => (
                    <div key={link.id ?? `m-${i}`} className="flex items-center justify-between gap-2">
                      <span className="text-sm text-gray-700 font-medium">
                        📍 {link.store_name}
                      </span>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-gradient-to-r from-pink-400 to-rose-500 hover:from-pink-500 hover:to-rose-600 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all shadow-sm hover:shadow-md"
                      >
                        View
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {shopLinks.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  Where to Buy:
                </p>
                <div className="flex flex-col gap-2">
                  {shopLinks.map((link, i) => (
                    <div key={link.id ?? `s-${i}`} className="flex items-center justify-between gap-2">
                      <span className="text-sm text-gray-700 font-medium">
                        {getStoreIcon(link.store_name)} {link.store_name}
                      </span>
                      <div className="flex items-center gap-2">
                        {link.price && (
                          <span className="text-sm font-bold text-gray-900">
                            {link.price} {link.currency ?? 'EGP'}
                          </span>
                        )}
                        {link.in_stock === false ? (
                          <span className="text-xs text-red-500 font-medium">Out of stock</span>
                        ) : (
                          <a
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-all shadow-sm hover:shadow-md"
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
      })()}

      {/* No buy links */}
      {(!product.buy_links || product.buy_links.length === 0) && (
        <div className="border-t border-gray-100 pt-3 mt-1">
          <p className="text-xs text-gray-400 text-center">No buy links available yet</p>
        </div>
      )}
    </div>
  )
}