"use client"

import React from "react"
import { PageContent } from "./page-content"
import { 
  BarChart3, 
  Users, 
  FolderKanban, 
  TrendingUp, 
  ArrowUpRight
} from "lucide-react"

const stats = [
  {
    title: "Total Projects",
    value: "24",
    icon: FolderKanban,
    change: "+12%",
    changeType: "positive" as const,
    color: "bg-navy-600",
    lightColor: "bg-navy-50"
  },
  {
    title: "Active Users", 
    value: "156",
    icon: Users,
    change: "+5%",
    changeType: "positive" as const,
    color: "bg-gray-300",
    lightColor: "bg-gray-50"
  },
  {
    title: "Test Cases",
    value: "1,234",
    icon: BarChart3,
    change: "+8%",
    changeType: "positive" as const,
    color: "bg-emerald-700",
    lightColor: "bg-emerald-50"
  },
  {
    title: "Success Rate",
    value: "94.2%",
    icon: TrendingUp,
    change: "+2.1%",
    changeType: "positive" as const,
    color: "bg-amber-600",
    lightColor: "bg-amber-50"
  }
]

const monthlyData = [
  { month: "Jan", testCases: 45, bugsFound: 8, coverage: 85 },
  { month: "Feb", testCases: 52, bugsFound: 6, coverage: 88 },
  { month: "Mar", testCases: 48, bugsFound: 9, coverage: 82 },
  { month: "Apr", testCases: 61, bugsFound: 4, coverage: 91 },
  { month: "May", testCases: 58, bugsFound: 7, coverage: 89 },
  { month: "Jun", testCases: 67, bugsFound: 3, coverage: 94 }
]

export function DashboardContent() {
  return (
    <PageContent maxWidth="full">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <div 
            key={index}
            className="group relative overflow-hidden rounded-lg bg-white border border-gray-100 p-4 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-xs font-medium text-gray-600 mb-1">
                  {stat.title}
                </p>
                <p className="text-2xl font-bold text-gray-900 mb-2">
                  {stat.value}
                </p>
                <div className="flex items-center gap-1">
                  <ArrowUpRight className="h-3 w-3 text-emerald-600" />
                  <span className="text-xs font-semibold text-emerald-700">
                    {stat.change}
                  </span>
                  <span className="text-xs text-gray-500">vs last month</span>
                </div>
              </div>
              <div className={`p-2 rounded-lg ${stat.lightColor} group-hover:scale-105 transition-transform duration-300`}>
                <stat.icon className={`h-5 w-5 text-white ${stat.color.replace('bg-', 'text-')}`} />
              </div>
            </div>
            
            {/* Gradient overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-transparent to-gray-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Monthly Chart */}
        <div>
          <div className="bg-white rounded-lg border border-gray-100 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-gray-900">Monthly Overview</h3>
              <select className="text-xs border border-gray-200 rounded-md px-2 py-1 bg-white">
                <option>Last 6 months</option>
                <option>This year</option>
              </select>
            </div>
            
            {/* Chart */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Test Cases</span>
                <span className="font-semibold text-navy-600">Max: 67</span>
              </div>
              
              <div className="flex items-end justify-between h-28 gap-1.5">
                {monthlyData.map((data, index) => (
                  <div key={index} className="flex flex-col items-center flex-1">
                    <div className="w-full bg-gray-100 rounded-t relative">
                      <div 
                        className="bg-gradient-to-t from-navy-600 to-navy-500 rounded-t transition-all duration-500 hover:from-navy-700 hover:to-navy-600"
                        style={{ 
                          height: `${(data.testCases / 70) * 100}%`,
                          minHeight: '6px'
                        }}
                        title={`${data.testCases} test cases`}
                      ></div>
                    </div>
                    <span className="text-[10px] text-gray-600 mt-1.5">{data.month}</span>
                    <span className="text-[10px] font-semibold text-gray-900">{data.testCases}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <h4 className="font-semibold text-gray-900 mb-3 text-sm">This Month</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-2 rounded-md bg-navy-50">
                  <div className="text-xl font-bold text-navy-700">67</div>
                  <div className="text-xs text-gray-600">Test Cases</div>
                </div>
                <div className="text-center p-2 rounded-md bg-emerald-50">
                  <div className="text-xl font-bold text-emerald-700">94%</div>
                  <div className="text-xs text-gray-600">Coverage</div>
                </div>
                <div className="text-center p-2 rounded-md bg-amber-50">
                  <div className="text-xl font-bold text-amber-700">3</div>
                  <div className="text-xs text-gray-600">Bugs Found</div>
                </div>
                <div className="text-center p-2 rounded-md bg-gray-50">
                  <div className="text-xl font-bold text-gray-700">Jun</div>
                  <div className="text-xs text-gray-600">Current</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageContent>
  )
} 