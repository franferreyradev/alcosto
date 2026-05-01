import { OrderStatus } from '../enums/order-status';
import { PaginatedResponse } from './pagination';
import { Order } from '../entities/order';

export interface CreateOrderItemRequest {
  product_code: number;
  quantity: number;
}

export interface CreateOrderRequest {
  customer_id: number;
  items: CreateOrderItemRequest[];
  notes?: string;
}

export interface UpdateOrderStatusRequest {
  status: OrderStatus;
}

export type OrderListResponse = PaginatedResponse<Order>;
