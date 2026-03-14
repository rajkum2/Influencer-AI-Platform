"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useInfluencers } from "@/lib/hooks/use-influencers";
import { useContentFeed } from "@/lib/hooks/use-content";
import { formatNumber, formatDate, getPlatformIcon } from "@/lib/utils";
import {
  Users,
  TrendingUp,
  FileText,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { data: influencersData } = useInfluencers({ page_size: 5 });
  const { data: feedData } = useContentFeed(7);

  const stats = [
    {
      title: "Total Influencers",
      value: influencersData?.total || 0,
      change: "+12%",
      trend: "up",
      icon: Users,
    },
    {
      title: "Active This Week",
      value: feedData?.total_new_week || 0,
      change: "+8%",
      trend: "up",
      icon: Activity,
    },
    {
      title: "New Content (24h)",
      value: feedData?.total_new_today || 0,
      change: "+24%",
      trend: "up",
      icon: FileText,
    },
    {
      title: "Avg Growth Rate",
      value: "12.5%",
      change: "-2%",
      trend: "down",
      icon: TrendingUp,
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your influencer universe
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            const TrendIcon = stat.trend === "up" ? ArrowUpRight : ArrowDownRight;
            return (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="flex items-center text-xs text-muted-foreground">
                    <TrendIcon
                      className={`mr-1 h-3 w-3 ${
                        stat.trend === "up" ? "text-green-500" : "text-red-500"
                      }`}
                    />
                    <span
                      className={
                        stat.trend === "up" ? "text-green-500" : "text-red-500"
                      }
                    >
                      {stat.change}
                    </span>
                    <span className="ml-1">from last month</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Trending Influencers */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Trending Influencers</CardTitle>
                <Link href="/dashboard/influencers">
                  <Button variant="ghost" size="sm">
                    View all
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {influencersData?.items?.slice(0, 5).map((influencer: any) => (
                  <div
                    key={influencer.id}
                    className="flex items-center gap-4 p-2 rounded-lg hover:bg-accent transition-colors"
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={influencer.profile_image_url} />
                      <AvatarFallback>
                        {influencer.full_name.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {influencer.full_name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {influencer.headline}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {formatNumber(influencer.total_followers)}
                      </p>
                      <p className="text-xs text-muted-foreground">followers</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Content */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Content</CardTitle>
                <Link href="/dashboard/content">
                  <Button variant="ghost" size="sm">
                    View all
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {feedData?.items?.slice(0, 5).map((content: any) => (
                  <div
                    key={content.id}
                    className="flex items-start gap-3 p-2 rounded-lg hover:bg-accent transition-colors"
                  >
                    <div className="text-lg">
                      {getPlatformIcon(content.platform)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium line-clamp-2">
                        {content.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-xs text-muted-foreground">
                          {content.influencer_name}
                        </p>
                        <span className="text-xs text-muted-foreground">•</span>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(content.published_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Technologies */}
        <Card>
          <CardHeader>
            <CardTitle>Top Technologies</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {[
                "Large Language Models",
                "AI Agents",
                "RAG",
                "Vector Databases",
                "AI Coding",
                "Computer Vision",
                "Multimodal AI",
                "AI Safety",
              ].map((tech) => (
                <Badge key={tech} variant="secondary" className="px-3 py-1">
                  {tech}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
