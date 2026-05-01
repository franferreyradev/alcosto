import { AdminRole } from '../enums/admin-role';

export interface AdminUser {
  id: number;
  email: string;
  role: AdminRole;
  is_active: boolean;
  created_at: string;
}
