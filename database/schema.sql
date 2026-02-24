-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Influencers table
CREATE TABLE influencers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  instagram_handle VARCHAR(255),
  tiktok_handle VARCHAR(255),
  platform VARCHAR(50) DEFAULT 'tiktok',
  followers INTEGER,
  profile_image TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Products table
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  influencer_name VARCHAR(255) NOT NULL,
  product_name VARCHAR(500) NOT NULL,
  brand VARCHAR(255),
  category VARCHAR(100),
  quote TEXT,
  video_url TEXT,
  platform VARCHAR(50) DEFAULT 'tiktok',
  video_timestamp VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Buy links table
CREATE TABLE buy_links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  store VARCHAR(100),
  price DECIMAL(10, 2),
  currency VARCHAR(10) DEFAULT 'EGP',
  url TEXT,
  in_stock BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_products_influencer ON products(influencer_name);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);

-- Full text search index
CREATE INDEX products_search_idx ON products
USING gin(to_tsvector('english',
  COALESCE(product_name, '') || ' ' ||
  COALESCE(brand, '') || ' ' ||
  COALESCE(category, '') || ' ' ||
  COALESCE(quote, '')
));

-- Row Level Security
ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE buy_links ENABLE ROW LEVEL SECURITY;

-- Public read access policies
CREATE POLICY "Public read influencers" ON influencers FOR SELECT USING (true);
CREATE POLICY "Public read products" ON products FOR SELECT USING (true);
CREATE POLICY "Public read buy_links" ON buy_links FOR SELECT USING (true);
