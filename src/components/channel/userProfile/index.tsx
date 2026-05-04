const userProfile = () => {
  return (
    <div className="flex w-full h-39 justify-start gap-8 px-6 py-4 rounded-xl border border-[#8257B4]">
      <div className="w-30 h-30 rounded-full bg-gray-500"></div>
      <div className="flex flex-col justify-start gap-3">
        <div className="w-full typo-title2 text-black">user name</div>
        <div className="flex flex-col w-full justify-start gap-2">
          <div className="typo-body1-medium text-black">youtube_name / youtube_channal</div>
          <div className="typo-body1-medium text-black">구독자 n명</div>
        </div>
      </div>
    </div>
  );
};

export default userProfile;
