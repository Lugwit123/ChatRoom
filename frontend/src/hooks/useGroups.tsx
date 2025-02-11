import { useQuery } from '@tanstack/react-query'
import { getGroups, getGroupMembers } from '../services/api'

export function useGroups() {
  // 获取所有群组
  const { data: groups, isLoading: isLoadingGroups } = useQuery({
    queryKey: ['groups'],
    queryFn: getGroups,
  })

  // 获取群组成员
  const useGroupMembers = (groupId: number) => {
    return useQuery({
      queryKey: ['groupMembers', groupId],
      queryFn: () => getGroupMembers(groupId),
      enabled: !!groupId,
    })
  }

  return {
    groups,
    isLoadingGroups,
    useGroupMembers,
  }
} 