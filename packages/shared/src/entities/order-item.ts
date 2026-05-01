import { Product } from './product';

export interface OrderItem {
  id: number;
  order_id: number;
  product_code: number;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface OrderItemWithProduct extends OrderItem {
  product: Pick<Product, 'code' | 'name' | 'slug' | 'image_url'>;
}
