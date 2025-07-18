import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface UserCardProps {
  id: string
  name: string
  email: string
  role: string
  status: 'active' | 'inactive'
  avatarUrl?: string
}

export function UserCard({ id, name, email, role, status, avatarUrl }: UserCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center gap-4">
        <Avatar className="h-12 w-12">
          <AvatarImage src={avatarUrl} alt={name} />
          <AvatarFallback>{name.slice(0, 2).toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <h3 className="text-lg font-semibold">{name}</h3>
          <p className="text-sm text-gray-500">{email}</p>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex justify-between items-center">
          <Badge variant={role === 'admin' ? 'default' : 'secondary'}>
            {role}
          </Badge>
          <Badge variant={status === 'active' ? 'default' : 'destructive'}>
            {status}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
} 