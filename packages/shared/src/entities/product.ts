import { Category } from './category';

export interface Product {
  code: number;
  name: string;
  description: string | null;
  price: number;
  stock: number;
  category_id: number | null;
  image_url: string | null;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductWithCategory extends Product {
  category: Category | null;
}
