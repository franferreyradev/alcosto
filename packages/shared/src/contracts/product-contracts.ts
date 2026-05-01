import { PaginatedResponse } from './pagination';
import { ProductWithCategory } from '../entities/product';

export interface CreateProductRequest {
  code: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  category_id?: number;
  image_url?: string;
}

export interface UpdateProductRequest {
  name?: string;
  description?: string;
  price?: number;
  stock?: number;
  category_id?: number;
  image_url?: string;
}

export interface UpdateProductStatusRequest {
  is_active: boolean;
}

export interface ProductExistsResponse {
  exists: boolean;
}

export interface ImageUploadResponse {
  image_url: string;
}

export type ProductListResponse = PaginatedResponse<ProductWithCategory>;
