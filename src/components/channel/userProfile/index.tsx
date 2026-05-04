import useChannelStore from '@/stores/useChannelStore';

const UserProfile = () => {
  const data = useChannelStore(s => s.data);
  const channel = data?.channel;

  return (
    <div className="flex w-full h-39 justify-start gap-8 px-6 py-4 rounded-xl border border-[#A594F9]">
      <div className="w-30 h-30 rounded-full bg-gray-500 overflow-hidden shrink-0">
        {channel?.profileImageUrl && (
          <img
            src={channel.profileImageUrl}
            alt={channel.name}
            className="w-full h-full object-cover"
          />
        )}
      </div>
      <div className="flex flex-col justify-start gap-3">
        <div className="w-full typo-title2 text-black">{channel?.channelId ?? 'channel ID'}</div>
        <div className="flex flex-col w-full justify-start gap-2">
          <div className="typo-body1-medium text-black">{channel?.name ?? 'youtube_name'}</div>
          <div className="typo-body1-medium text-black">
            구독자 {channel?.subscriberCount ? channel.subscriberCount.toLocaleString() : 'n'}명
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
