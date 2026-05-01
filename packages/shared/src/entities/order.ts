import { OrderStatus } from '../enums/order-status';
import { Customer } from './customer';
import { OrderItemWithProduct } from './order-item';

export interface Order {
  id: number;
  customer_id: number;
  status: OrderStatus;
  total_amount: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderDetail extends Order {
  customer: Customer;
  items: OrderItemWithProduct[];
}
